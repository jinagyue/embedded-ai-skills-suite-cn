#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

from _common import find_project_root, load_json, write_json
from analyze_project import analyze
from generate_arch_docs import render_architecture, render_module_map, render_task_design
from include_graph import write_dot, write_mermaid
from external_embeddedskills_adapter import invoke as invoke_external

SUITE_ROOT = Path(__file__).resolve().parents[2]

def newest_elf(root: Path) -> Path | None:
    candidates = []
    skip = {'.git', 'Drivers', 'Middlewares', '.embedded-ai'}
    for path in root.rglob('*.elf'):
        if any(part in skip for part in path.parts):
            continue
        try:
            candidates.append((path.stat().st_mtime, path))
        except OSError:
            pass
    return max(candidates, default=(0, None), key=lambda x: x[0])[1]

def newest_map(root: Path) -> Path | None:
    candidates = []
    skip = {'.git', 'Drivers', 'Middlewares', '.embedded-ai'}
    for path in root.rglob('*.map'):
        if any(part in skip for part in path.parts):
            continue
        try:
            candidates.append((path.stat().st_mtime, path))
        except OSError:
            pass
    return max(candidates, default=(0, None), key=lambda x: x[0])[1]


def load_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def run_ioc_consistency(root: Path, debug_dir: Path) -> tuple[dict | None, list[dict]]:
    tool = SUITE_ROOT / 'shared' / 'scripts' / 'ioc_source_consistency.py'
    if not tool.exists():
        return None, []
    json_out = debug_dir / 'ioc_source_consistency.json'
    md_out = debug_dir / 'IOC_SOURCE_CONSISTENCY.md'
    cmd = f'"{sys.executable}" "{tool}" "{root}" --output "{json_out}" --report "{md_out}"'
    r = run_shell(cmd, root)
    r['name'] = 'ioc-source-consistency'
    r['summary'] = '检查 CubeMX .ioc 与源码外设/GPIO/NVIC/DMA/FreeRTOS 配置漂移'
    r['output_file'] = str(json_out)
    data = load_json_file(json_out) if json_out.exists() else {}
    findings = [{'source': 'ioc_consistency', **f} for f in data.get('findings', [])]
    return r, findings


def run_map_analysis(root: Path, debug_dir: Path) -> dict | None:
    map_file = newest_map(root)
    if map_file is None:
        return None
    tool = SUITE_ROOT / 'tools' / 'keil_map_analyzer' / 'keil_map_analyzer.py'
    if not tool.exists():
        return None
    json_out = debug_dir / 'keil_map_analysis.json'
    md_out = debug_dir / 'KEIL_MAP_REPORT.md'
    cmd = f'"{sys.executable}" "{tool}" "{map_file}" --json-out "{json_out}" --report "{md_out}"'
    r = run_shell(cmd, root)
    r['name'] = 'keil-map-analysis'
    r['summary'] = f'已分析 MAP：{map_file.name}'
    r['output_file'] = str(json_out)
    return r


def run_freertos_runtime_analysis(runtime_log: Path, debug_dir: Path, cfg: dict) -> tuple[dict | None, list[dict]]:
    if not runtime_log.exists():
        return None, []
    text = runtime_log.read_text(encoding='utf-8', errors='replace')
    if '@FREERTOS_TASK' not in text and '@FREERTOS_SNAPSHOT' not in text:
        return None, []
    tool = SUITE_ROOT / 'tools' / 'freertos_runtime' / 'freertos_runtime_analyzer.py'
    if not tool.exists():
        return None, []
    rcfg = cfg.get('freertos_runtime', {})
    json_out = debug_dir / 'freertos_runtime.json'
    md_out = debug_dir / 'FREERTOS_RUNTIME.md'
    cmd = (f'"{sys.executable}" "{tool}" "{runtime_log}" '
           f'--stack-warn-words {int(rcfg.get("stack_warn_words", 64))} '
           f'--stack-critical-words {int(rcfg.get("stack_critical_words", 24))} '
           f'--stack-word-bytes {int(rcfg.get("stack_word_bytes", 4))} '
           f'--json-out "{json_out}" --report "{md_out}"')
    if rcfg.get('heap_warn_bytes') is not None:
        cmd += f' --heap-warn-bytes {int(rcfg["heap_warn_bytes"])}'
    r = run_shell(cmd, runtime_log.parent)
    r['name'] = 'freertos-runtime-analysis'
    r['summary'] = '已解析 FreeRTOS Task/Stack/Heap 运行时证据'
    r['output_file'] = str(json_out)
    data = load_json_file(json_out) if json_out.exists() else {}
    findings = [{'source': 'freertos_runtime', **f} for f in data.get('findings', [])]
    return r, findings


def run_hardfault_decode(runtime_log: Path, root: Path, debug_dir: Path, cfg: dict) -> tuple[dict | None, list[dict]]:
    if not runtime_log.exists():
        return None, []
    text = runtime_log.read_text(encoding='utf-8', errors='replace')
    if not re.search(r'HardFault|CFSR\s*[:=]|HFSR\s*[:=]|BusFault|UsageFault|MemManage', text, re.I):
        return None, []
    tool = SUITE_ROOT / 'tools' / 'hardfault_decoder' / 'hardfault_decoder.py'
    if not tool.exists():
        return None, []
    json_out = debug_dir / 'hardfault_analysis.json'
    md_out = debug_dir / 'HARDFAULT_REPORT.md'
    elf = newest_elf(root)
    cmd = f'"{sys.executable}" "{tool}" --log "{runtime_log}" --json-out "{json_out}" --report "{md_out}"'
    if elf:
        cmd += f' --elf "{elf}"'
    addr_tool = cfg.get('auto_debug', {}).get('addr2line_tool')
    if addr_tool:
        cmd += f' --tool "{addr_tool}"'
    r = run_shell(cmd, root)
    r['name'] = 'hardfault-decode'
    r['summary'] = '已解码 Cortex-M Fault 状态寄存器并尝试 addr2line 定位 PC/LR'
    r['output_file'] = str(json_out)
    data = load_json_file(json_out) if json_out.exists() else {}
    findings = []
    for item in data.get('diagnosis', []):
        findings.append({'source': 'hardfault_decoder', 'severity': 'critical', 'type': 'hardfault_diagnosis', 'message': item})
    return r, findings


def run_elf_analysis(root: Path, debug_dir: Path) -> dict | None:
    elf = newest_elf(root)
    if elf is None:
        return None
    tool = SUITE_ROOT / 'tools' / 'elf_analyzer' / 'elf_analyzer.py'
    if not tool.exists():
        return None
    json_out = debug_dir / 'elf_analysis.json'
    md_out = debug_dir / 'ELF_REPORT.md'
    cmd = f'"{sys.executable}" "{tool}" "{elf}" --all --json-out "{json_out}" --report "{md_out}"'
    r = run_shell(cmd, root)
    r['name'] = 'elf-analysis'
    r['summary'] = f'已分析固件 ELF：{elf.name}'
    r['output_file'] = str(json_out)
    return r

def run_serial_evidence(root: Path, cfg: dict, debug_dir: Path) -> dict | None:
    scfg = cfg.get('serial', {})
    port = scfg.get('port')
    if not port:
        return None
    tool = SUITE_ROOT / 'tools' / 'serial_monitor' / 'serial_monitor.py'
    if not tool.exists():
        return None
    baud = int(scfg.get('baud', 115200))
    duration = float(scfg.get('duration_s', 5))
    mode = str(scfg.get('mode', 'both'))
    log = debug_dir / 'serial.log'
    jsonl = debug_dir / 'serial_evidence.jsonl'
    cmd = (f'"{sys.executable}" "{tool}" -p "{port}" -b {baud} '
           f'--mode {mode} --duration {duration} --log "{log}" --jsonl "{jsonl}" --no-input')
    r = run_shell(cmd, root, timeout=max(duration + 5, 10))
    r['name'] = 'serial-observe'
    r['summary'] = f'串口采证 {port} @ {baud}，{duration}s'
    r['output_file'] = str(log)
    return r

SIGNATURES = [
    ('hardfault', 'critical', re.compile(r'HardFault|HFSR|CFSR|UsageFault|BusFault|MemManage', re.I)),
    ('stack_overflow', 'critical', re.compile(r'stack overflow|vApplicationStackOverflowHook|uxTaskGetStackHighWaterMark', re.I)),
    ('assert', 'high', re.compile(r'configASSERT|assert(?:ion)? failed', re.I)),
    ('watchdog_reset', 'high', re.compile(r'watchdog|IWDG|WWDG|wdg.*reset|reset.*wdg', re.I)),
    ('heap_memory', 'high', re.compile(r'malloc failed|out of memory|heap.*fail', re.I)),
    ('linker_overflow', 'high', re.compile(r'region .* overflowed|will not fit in region|No space in execution regions', re.I)),
    ('undefined_symbol', 'high', re.compile(r'undefined reference|L6218E: Undefined symbol|identifier .* is undefined', re.I)),
    ('compile_error', 'high', re.compile(r'\berror:\b|fatal error|Error\[Pe\d+\]|\.c\(\d+\): error', re.I)),
    ('dma', 'medium', re.compile(r'\bDMA\b.*(?:error|fail|timeout)|(?:error|fail|timeout).*\bDMA\b', re.I)),
    ('uart', 'medium', re.compile(r'\bUART\b.*(?:error|overrun|ORE|timeout)|(?:error|overrun|timeout).*\bUART\b', re.I)),
    ('i2c', 'medium', re.compile(r'\bI2C\b.*(?:BUSY|NACK|error|timeout)|(?:NACK|error|timeout).*\bI2C\b', re.I)),
    ('fatfs', 'medium', re.compile(r'FatFs|FR_(?:DISK_ERR|INT_ERR|NOT_READY|NO_FILE|DENIED)', re.I)),
]


def run_shell(command: str, cwd: Path, timeout: float | None = None) -> dict:
    started = time.time()
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout,
    )
    return {
        'command': command,
        'returncode': proc.returncode,
        'stdout': proc.stdout,
        'stderr': proc.stderr,
        'duration_s': round(time.time() - started, 3),
        'status': 'ok' if proc.returncode == 0 else 'error',
    }


def classify_text(text: str) -> list[dict]:
    hits = []
    for name, severity, pat in SIGNATURES:
        matches = list(pat.finditer(text))
        if matches:
            samples = []
            lines = text.splitlines()
            for m in matches[:5]:
                line_no = text.count('\n', 0, m.start()) + 1
                if 1 <= line_no <= len(lines):
                    samples.append({'line': line_no, 'text': lines[line_no - 1][:400]})
            hits.append({'type': name, 'severity': severity, 'count': len(matches), 'samples': samples})
    return hits


def merge_findings(project_model: dict, runtime_hits: list[dict], external: dict | None, extra_findings: list[dict] | None = None) -> list[dict]:
    out = []
    for f in project_model.get('resource_audit', {}).get('findings', []):
        out.append({'source': 'resource_audit', **f})
    for f in project_model.get('hal_leaks', {}).get('findings', []):
        out.append({'source': 'hal_leak', **f})
    for f in project_model.get('include_graph', {}).get('violations', []):
        out.append({'source': 'dependency', **f})
    for f in runtime_hits:
        out.append({'source': 'runtime', **f, 'message': f"Runtime/build signature detected: {f['type']} ({f['count']})"})
    if external and external.get('status') == 'error':
        out.append({'source': 'external_debug', 'severity': 'medium', 'type': 'external_backend_error', 'message': str(external.get('error'))})
    if extra_findings:
        out.extend(extra_findings)
    return out


def render_debug_report(root: Path, model: dict, actions: list[dict], hits: list[dict], findings: list[dict]) -> str:
    lines = [
        '# 自动调试报告', '',
        '> 由嵌入式 AI Skills V0.4 中文版自动调试编排器生成。', '',
        f'- 工程：`{root}`',
        f'- 静态风险分：**{model.get("risk_score", 0)}**',
        f'- 已执行动作：**{len(actions)}**',
        f'- 运行/构建故障特征：**{len(hits)}**', '',
        '## 证据时间线', '',
    ]
    if actions:
        for i, a in enumerate(actions, 1):
            lines.append(f"### {i}. {a.get('name', 'action')}")
            lines.append('')
            if a.get('command'):
                lines.append(f"- Command: `{a['command']}`")
            lines.append(f"- Status: `{a.get('status')}`")
            if 'returncode' in a:
                lines.append(f"- Return code: `{a.get('returncode')}`")
            if a.get('summary'):
                lines.append(f"- Summary: {a['summary']}")
            if a.get('output_file'):
                lines.append(f"- Output: `{a['output_file']}`")
            lines.append('')
    else:
        lines.append('_未执行动态动作，本报告仅包含静态证据。_\n')

    lines += ['## 检测到的故障特征', '']
    if hits:
        for h in hits:
            lines.append(f"- **{h['severity'].upper()}** `{h['type']}` × {h['count']}")
            for s in h.get('samples', [])[:3]:
                lines.append(f"  - L{s['line']}: `{s['text']}`")
    else:
        lines.append('未检测到已知的运行/构建故障特征。')

    lines += ['', '## 综合发现', '']
    if findings:
        for f in findings[:100]:
            lines.append(f"- **{str(f.get('severity', 'info')).upper()}** [{f.get('source')}/{f.get('type', 'finding')}] {f.get('message', '')}")
    else:
        lines.append('未发现问题。')

    lines += ['', '## AI 修复闭环约束', '',
              '1. 只做有证据支撑的最小修改，不重写无关模块。',
              '2. 编译/链接错误修复后才能进入烧录。',
              '3. CRITICAL/HIGH 的 Fault、ISR、IRQ、栈问题优先于业务逻辑。',
              '4. 每次补丁后执行：重新构建 → 静态检查 → 可选烧录 → 观测 → Fault/RTOS 报告。',
              '5. 达到最大迭代次数或证据不再改善时停止。',
              '6. 除非用户/项目显式允许，否则绝不自动烧录。', '']
    return '\n'.join(lines)


def default_config(root: Path) -> dict:
    return {
        'schema_version': '0.4',
        'project': {'root': str(root)},
        'analysis': {'strict_osal': False},
        'commands': {'build': None, 'test': None, 'flash': None, 'observe': None},
        'serial': {'port': None, 'baud': 115200, 'duration_s': 5, 'mode': 'both'},
        'freertos_runtime': {'stack_warn_words': 64, 'stack_critical_words': 24, 'stack_word_bytes': 4, 'heap_warn_bytes': None},
        'auto_debug': {
            'max_iterations': 3,
            'analyze_elf': True,
            'analyze_map': True,
            'check_ioc_consistency': True,
            'decode_hardfault': True,
            'analyze_freertos_runtime': True,
            'addr2line_tool': None,
            'allow_flash': False,
            'external_embeddedskills_root': None,
            'external_debug_backend': 'auto',
            'external_observe_backend': 'auto',
        },
    }


def load_config(root: Path, config_path: Path | None) -> tuple[dict, Path]:
    path = config_path or (root / '.embedded-ai' / 'config.json')
    if not path.exists():
        cfg = default_config(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, cfg)
        return cfg, path
    cfg = load_json(path, default_config(root))
    return cfg, path


def run_static(root: Path, cfg: dict, report_dir: Path) -> dict:
    model = analyze(root, strict_osal=bool(cfg.get('analysis', {}).get('strict_osal')))
    write_json(root / '.embedded-ai' / 'project_model.json', model)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / 'ARCHITECTURE.md').write_text(render_architecture(model), encoding='utf-8')
    (report_dir / 'TASK_DESIGN.md').write_text(render_task_design(model), encoding='utf-8')
    (report_dir / 'MODULE_MAP.md').write_text(render_module_map(model), encoding='utf-8')
    write_dot(model['include_graph'], report_dir / 'include_graph.dot')
    write_mermaid(model['include_graph'], report_dir / 'include_graph.mmd')
    return model


def maybe_external(cfg: dict, root: Path, action: str, backend_key: str | None = None) -> dict | None:
    acfg = cfg.get('auto_debug', {})
    ext_root = acfg.get('external_embeddedskills_root')
    if not ext_root:
        return None
    ext = Path(ext_root).expanduser().resolve()
    extra = []
    if backend_key:
        backend = acfg.get(backend_key, 'auto')
        if backend and backend != 'auto':
            flag = '--debug-backend' if 'debug' in backend_key else '--observe-backend'
            extra.extend([flag, backend])
    return invoke_external(ext, root, action, extra)


def main() -> None:
    ap = argparse.ArgumentParser(description='面向 AI 的中文嵌入式自动调试编排器')
    ap.add_argument('action', choices=['plan', 'static', 'diagnose', 'cycle'], nargs='?', default='plan')
    ap.add_argument('--workspace', default='.')
    ap.add_argument('--config')
    ap.add_argument('--allow-flash', action='store_true', help='本次运行显式允许烧录固件')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    root = find_project_root(args.workspace)
    cfg, cfg_path = load_config(root, Path(args.config).resolve() if args.config else None)
    report_dir = root / '.embedded-ai' / 'reports'
    debug_dir = root / '.embedded-ai' / 'debug'
    debug_dir.mkdir(parents=True, exist_ok=True)
    model = run_static(root, cfg, report_dir)

    actions = []
    runtime_text = ''
    external_result = None
    extra_findings: list[dict] = []

    if bool(cfg.get('auto_debug', {}).get('check_ioc_consistency', True)):
        ir, ifind = run_ioc_consistency(root, debug_dir)
        if ir:
            actions.append(ir)
        extra_findings.extend(ifind)

    if args.action in {'diagnose', 'cycle'}:
        external_result = maybe_external(cfg, root, 'diagnose')
        if external_result:
            actions.append({'name': 'external-diagnose', 'status': external_result.get('status'), 'summary': external_result.get('summary') or str(external_result.get('error'))})

    commands = cfg.get('commands', {})
    if args.action == 'cycle':
        build_cmd = commands.get('build')
        if build_cmd:
            r = run_shell(build_cmd, root)
            r['name'] = 'build'
            log = debug_dir / 'build.log'
            log.write_text((r.get('stdout') or '') + '\n' + (r.get('stderr') or ''), encoding='utf-8')
            r['output_file'] = str(log)
            actions.append(r)
            runtime_text += '\n' + log.read_text(encoding='utf-8', errors='replace')
        elif cfg.get('auto_debug', {}).get('external_embeddedskills_root'):
            r = maybe_external(cfg, root, 'build-debug', 'external_debug_backend')
            external_result = r
            actions.append({'name': 'external-build-debug', 'status': (r or {}).get('status'), 'summary': (r or {}).get('summary') or str((r or {}).get('error'))})
            runtime_text += '\n' + json.dumps(r or {}, ensure_ascii=False)

        test_cmd = commands.get('test')
        if test_cmd:
            r = run_shell(test_cmd, root)
            r['name'] = 'test'
            log = debug_dir / 'test.log'
            log.write_text((r.get('stdout') or '') + '\n' + (r.get('stderr') or ''), encoding='utf-8')
            r['output_file'] = str(log)
            actions.append(r)
            runtime_text += '\n' + log.read_text(encoding='utf-8', errors='replace')

        if bool(cfg.get('auto_debug', {}).get('analyze_map', True)):
            mr = run_map_analysis(root, debug_dir)
            if mr:
                actions.append(mr)
                runtime_text += '\n' + (mr.get('stdout') or '') + '\n' + (mr.get('stderr') or '')

        if bool(cfg.get('auto_debug', {}).get('analyze_elf', True)):
            er = run_elf_analysis(root, debug_dir)
            if er:
                actions.append(er)
                runtime_text += '\n' + (er.get('stdout') or '') + '\n' + (er.get('stderr') or '')

        allow_flash = args.allow_flash or bool(cfg.get('auto_debug', {}).get('allow_flash'))
        if allow_flash:
            flash_cmd = commands.get('flash')
            if flash_cmd:
                r = run_shell(flash_cmd, root)
                r['name'] = 'flash'
                log = debug_dir / 'flash.log'
                log.write_text((r.get('stdout') or '') + '\n' + (r.get('stderr') or ''), encoding='utf-8')
                r['output_file'] = str(log)
                actions.append(r)
                runtime_text += '\n' + log.read_text(encoding='utf-8', errors='replace')
            elif cfg.get('auto_debug', {}).get('external_embeddedskills_root'):
                r = maybe_external(cfg, root, 'build-flash')
                external_result = r
                actions.append({'name': 'external-build-flash', 'status': (r or {}).get('status'), 'summary': (r or {}).get('summary') or str((r or {}).get('error'))})
                runtime_text += '\n' + json.dumps(r or {}, ensure_ascii=False)
        else:
            actions.append({'name': 'flash', 'status': 'skipped', 'summary': '安全策略默认禁止烧录；如需烧录请显式使用 --allow-flash 或配置 auto_debug.allow_flash=true'})

        observe_cmd = commands.get('observe')
        if observe_cmd:
            r = run_shell(observe_cmd, root)
            r['name'] = 'observe'
            log = debug_dir / 'observe.log'
            log.write_text((r.get('stdout') or '') + '\n' + (r.get('stderr') or ''), encoding='utf-8')
            r['output_file'] = str(log)
            actions.append(r)
            runtime_text += '\n' + log.read_text(encoding='utf-8', errors='replace')
        elif cfg.get('auto_debug', {}).get('external_embeddedskills_root'):
            r = maybe_external(cfg, root, 'observe', 'external_observe_backend')
            actions.append({'name': 'external-observe-plan', 'status': (r or {}).get('status'), 'summary': (r or {}).get('summary') or str((r or {}).get('error'))})
            runtime_text += '\n' + json.dumps(r or {}, ensure_ascii=False)

        # 若未配置显式 observe 命令，也可用串口作为通用证据源。
        sr = run_serial_evidence(root, cfg, debug_dir)
        if sr:
            actions.append(sr)
            if Path(sr.get('output_file','')).exists():
                runtime_text += '\n' + Path(sr['output_file']).read_text(encoding='utf-8', errors='replace')

    runtime_log = debug_dir / 'runtime_combined.log'
    runtime_log.write_text(runtime_text, encoding='utf-8')

    if bool(cfg.get('auto_debug', {}).get('analyze_freertos_runtime', True)):
        rr, rfind = run_freertos_runtime_analysis(runtime_log, debug_dir, cfg)
        if rr:
            actions.append(rr)
        extra_findings.extend(rfind)

    if bool(cfg.get('auto_debug', {}).get('decode_hardfault', True)):
        hr, hfind = run_hardfault_decode(runtime_log, root, debug_dir, cfg)
        if hr:
            actions.append(hr)
        extra_findings.extend(hfind)

    hits = classify_text(runtime_text)
    findings = merge_findings(model, hits, external_result, extra_findings)
    report = render_debug_report(root, model, actions, hits, findings)
    (debug_dir / 'DEBUG_REPORT.md').write_text(report, encoding='utf-8')
    result = {
        'status': 'ok',
        'action': args.action,
        'project': str(root),
        'config': str(cfg_path),
        'project_model': str(root / '.embedded-ai' / 'project_model.json'),
        'architecture_report': str(report_dir / 'ARCHITECTURE.md'),
        'task_report': str(report_dir / 'TASK_DESIGN.md'),
        'module_map': str(report_dir / 'MODULE_MAP.md'),
        'debug_report': str(debug_dir / 'DEBUG_REPORT.md'),
        'actions': actions,
        'runtime_signatures': hits,
        'finding_count': len(findings),
        'safe_flash_default': not (args.allow_flash or bool(cfg.get('auto_debug', {}).get('allow_flash'))),
    }
    write_json(debug_dir / 'debug_result.json', result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"静态工程模型：{result['project_model']}")
        print(f"架构文档目录：{report_dir}")
        print(f"自动调试报告：{result['debug_report']}")
        if args.action == 'cycle' and result['safe_flash_default']:
            print('本次未允许烧录，这是默认安全策略。')


if __name__ == '__main__':
    main()
