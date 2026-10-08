#!/usr/bin/env python3
"""STM32CubeMX .ioc 与源码资源一致性检查。

定位 CubeMX 配置与当前源码/手工修改之间的漂移：
- IOC 已启用外设，但源码缺少对应 MX_*_Init / 实例引用；
- IOC 启用 NVIC，但源码未找到 SetPriority / EnableIRQ；
- IOC 优先级与源码 HAL_NVIC_SetPriority 不一致；
- IOC GPIO label 与 main.h/头文件宏不一致；
- IOC 有 DMA 配置但源码缺少 DMA 初始化/句柄/链接证据；
- FreeRTOS 在 IOC 中启用，但源码缺少任务/Kernel 初始化证据。

这是启发式一致性检查，不替代 CubeMX 重新生成后的 diff 审查。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from _common import find_project_root, iter_source_files, norm_rel, read_text, write_json
from parse_ioc import discover_ioc, parse_ioc_file

NVIC_PRIO_RE = re.compile(r'HAL_NVIC_SetPriority\s*\(\s*([A-Za-z0-9_]+_IRQn)\s*,\s*([^,\)]+)\s*,\s*([^\)]+)\)')
NVIC_ENABLE_RE = re.compile(r'HAL_NVIC_EnableIRQ\s*\(\s*([A-Za-z0-9_]+_IRQn)\s*\)')
GPIO_PIN_MACRO_RE = re.compile(r'^\s*#define\s+([A-Za-z_]\w*)_Pin\s+GPIO_PIN_(\d+)\b', re.M)
GPIO_PORT_MACRO_RE = re.compile(r'^\s*#define\s+([A-Za-z_]\w*)_GPIO_Port\s+GPIO([A-K])\b', re.M)


def parse_int_expr(expr: str) -> int | None:
    expr = expr.strip()
    try:
        return int(expr, 0)
    except ValueError:
        m = re.search(r'\b(\d+)\b', expr)
        return int(m.group(1)) if m else None


def source_corpus(root: Path) -> tuple[str, list[dict[str, str]]]:
    rows = []
    all_text = []
    for path in iter_source_files(root, include_generated=True):
        rel = norm_rel(path, root)
        text = read_text(path)
        rows.append({'file': rel, 'text': text})
        all_text.append(f'\n/* FILE:{rel} */\n{text}')
    return '\n'.join(all_text), rows


def expected_peripherals(ioc: dict[str, Any]) -> list[str]:
    names = set(ioc.get('peripherals', {}).keys())
    for ip in ioc.get('ips', []):
        if re.fullmatch(r'(?:USART|UART|SPI|I2C|I3C|ADC|DAC|TIM|LPTIM|CAN|FDCAN|SDIO|SDMMC|RTC|RNG|USB|ETH)\d*', ip, re.I):
            names.add(ip)
    return sorted(names)


def peripheral_init_patterns(name: str) -> list[re.Pattern[str]]:
    u = name.upper()
    pats = [re.compile(rf'\bMX_{re.escape(u)}_Init\s*\(', re.I)]
    if u.startswith('USART'):
        n = u[len('USART'):]
        pats += [re.compile(rf'\bMX_USART{re.escape(n)}_UART_Init\s*\(', re.I), re.compile(rf'\bMX_UART{re.escape(n)}_Init\s*\(', re.I)]
    elif u.startswith('UART'):
        n = u[len('UART'):]
        pats += [re.compile(rf'\bMX_UART{re.escape(n)}_Init\s*\(', re.I), re.compile(rf'\bMX_USART{re.escape(n)}_UART_Init\s*\(', re.I)]
    elif u.startswith('USB'):
        pats += [re.compile(r'\bMX_USB_(?:DEVICE|HOST)_Init\s*\(', re.I)]
    return pats


def pin_num_from_name(pin: str) -> tuple[str, int] | None:
    m = re.fullmatch(r'P([A-K])(\d{1,2})', pin)
    if not m:
        return None
    return m.group(1), int(m.group(2))


def audit(root: Path, ioc_path: Path | None = None) -> dict[str, Any]:
    if ioc_path is None:
        ioc_path = discover_ioc(root)
    if ioc_path is None or not ioc_path.exists():
        return {'project': str(root), 'ioc_file': None, 'findings': [{'severity': 'high', 'type': 'ioc_missing', 'message': '未找到唯一 .ioc 文件，请使用 --ioc 指定'}], 'summary': {'critical': 0, 'high': 1, 'medium': 0, 'low': 0}}

    ioc = parse_ioc_file(ioc_path)
    corpus, files = source_corpus(root)
    findings: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {'expected_peripherals': expected_peripherals(ioc), 'source_files': len(files)}

    # 1) 外设启用与 init/实例证据
    for periph in evidence['expected_peripherals']:
        init_hit = any(p.search(corpus) for p in peripheral_init_patterns(periph))
        token_hit = bool(re.search(rf'\b{re.escape(periph)}\b', corpus, re.I))
        if not init_hit and not token_hit:
            findings.append({'severity': 'high', 'type': 'peripheral_missing_in_source', 'peripheral': periph,
                             'message': f'IOC 启用了 {periph}，但源码中未找到对应 MX_*_Init 或实例引用'})
        elif not init_hit:
            findings.append({'severity': 'low', 'type': 'peripheral_init_not_found', 'peripheral': periph,
                             'message': f'IOC 启用了 {periph}，源码有实例引用但未找到标准 MX_*_Init；若使用 LL/自定义初始化请人工确认'})

    # 2) NVIC 优先级和 EnableIRQ
    src_prio: dict[str, dict[str, Any]] = {}
    src_enable = set()
    for row in files:
        for m in NVIC_PRIO_RE.finditer(row['text']):
            src_prio[m.group(1)] = {'priority': parse_int_expr(m.group(2)), 'sub_priority': parse_int_expr(m.group(3)), 'file': row['file']}
        for m in NVIC_ENABLE_RE.finditer(row['text']):
            src_enable.add(m.group(1))
    evidence['source_nvic_priorities'] = src_prio
    evidence['source_nvic_enabled'] = sorted(src_enable)

    for irq in ioc.get('nvic', []):
        if irq.get('enabled') is not True:
            continue
        name = irq['irq']
        cfg = src_prio.get(name)
        if cfg is None:
            findings.append({'severity': 'medium', 'type': 'nvic_priority_missing_in_source', 'irq': name,
                             'message': f'IOC 启用了 {name}，但源码未找到 HAL_NVIC_SetPriority({name}, ...)'})
        elif irq.get('preempt_priority') is not None and cfg.get('priority') is not None and irq['preempt_priority'] != cfg['priority']:
            findings.append({'severity': 'high', 'type': 'nvic_priority_mismatch', 'irq': name,
                             'ioc_priority': irq['preempt_priority'], 'source_priority': cfg['priority'], 'file': cfg['file'],
                             'message': f"{name} 优先级漂移：IOC={irq['preempt_priority']}，源码={cfg['priority']}"})
        if name not in src_enable:
            findings.append({'severity': 'low', 'type': 'nvic_enable_not_found', 'irq': name,
                             'message': f'IOC 启用了 {name}，但源码未找到 HAL_NVIC_EnableIRQ；可能由其他初始化路径负责，需确认'})

    # 3) GPIO label -> *_Pin / *_GPIO_Port
    pin_macros: dict[str, int] = {}
    port_macros: dict[str, str] = {}
    for row in files:
        for m in GPIO_PIN_MACRO_RE.finditer(row['text']):
            pin_macros[m.group(1)] = int(m.group(2))
        for m in GPIO_PORT_MACRO_RE.finditer(row['text']):
            port_macros[m.group(1)] = m.group(2)
    for p in ioc.get('pins', []):
        label = p.get('label')
        if not label:
            continue
        pp = pin_num_from_name(p.get('pin', ''))
        if pp is None:
            continue
        port_letter, pin_num = pp
        if label not in pin_macros and label not in port_macros:
            findings.append({'severity': 'medium', 'type': 'gpio_label_missing_in_source', 'label': label, 'pin': p['pin'],
                             'message': f'IOC GPIO label {label}({p["pin"]}) 未在源码头文件中找到 {label}_Pin / {label}_GPIO_Port'})
            continue
        if label in pin_macros and pin_macros[label] != pin_num:
            findings.append({'severity': 'high', 'type': 'gpio_pin_mismatch', 'label': label, 'ioc_pin': p['pin'], 'source_pin': pin_macros[label],
                             'message': f'GPIO {label} 引脚漂移：IOC={p["pin"]}，源码 GPIO_PIN_{pin_macros[label]}'})
        if label in port_macros and port_macros[label] != port_letter:
            findings.append({'severity': 'high', 'type': 'gpio_port_mismatch', 'label': label, 'ioc_pin': p['pin'], 'source_port': port_macros[label],
                             'message': f'GPIO {label} 端口漂移：IOC=P{port_letter}，源码=GPIO{port_macros[label]}'})

    # 4) DMA 基本一致性
    if ioc.get('dma'):
        has_dma_init = bool(re.search(r'\bMX_DMA_Init\s*\(', corpus))
        has_dma_handle = bool(re.search(r'\bDMA_HandleTypeDef\s+\w+', corpus))
        has_dma_link = bool(re.search(r'\b__HAL_LINKDMA\s*\(', corpus))
        evidence['dma'] = {'ioc_entries': len(ioc['dma']), 'mx_dma_init': has_dma_init, 'handle': has_dma_handle, 'link': has_dma_link}
        if not has_dma_init:
            findings.append({'severity': 'medium', 'type': 'dma_init_missing_in_source', 'message': 'IOC 存在 DMA 配置，但源码未找到 MX_DMA_Init()'})
        if not (has_dma_handle or has_dma_link):
            findings.append({'severity': 'medium', 'type': 'dma_binding_missing_in_source', 'message': 'IOC 存在 DMA 配置，但源码未找到 DMA_HandleTypeDef 或 __HAL_LINKDMA 绑定证据'})

    # 5) FreeRTOS 基本一致性
    rtos_enabled = any(str(x).upper() == 'FREERTOS' for x in ioc.get('ips', [])) or bool(ioc.get('freertos'))
    if rtos_enabled:
        has_rtos = bool(re.search(r'\b(osKernelInitialize|osThreadNew|xTaskCreate|MX_FREERTOS_Init|vTaskStartScheduler)\b', corpus))
        evidence['freertos_source_evidence'] = has_rtos
        if not has_rtos:
            findings.append({'severity': 'high', 'type': 'freertos_missing_in_source', 'message': 'IOC 启用了 FreeRTOS，但源码未找到常见 Kernel/Task 初始化证据'})

    summary = {s: sum(1 for f in findings if f['severity'] == s) for s in ('critical','high','medium','low')}
    return {
        'project': str(root),
        'ioc_file': str(ioc_path),
        'findings': findings,
        'summary': summary,
        'evidence': evidence,
        'notes': [
            '本工具是启发式漂移检查，LL/自定义 BSP/手写初始化可能产生低置信度提示。',
            '最可靠的 CubeMX 漂移验证仍是保存工程后重新生成到临时目录并做 diff。',
        ],
    }


def render_md(r: dict[str, Any]) -> str:
    s = r['summary']
    lines = ['# STM32CubeMX `.ioc` / 源码一致性报告', '', f"- 工程：`{r['project']}`", f"- IOC：`{r['ioc_file']}`", f"- Critical：**{s['critical']}** / High：**{s['high']}** / Medium：**{s['medium']}** / Low：**{s['low']}**", '', '## 发现', '']
    if r['findings']:
        for f in r['findings']:
            lines.append(f"- **{f['severity'].upper()}** `{f['type']}`：{f['message']}")
    else:
        lines.append('未发现已知的一致性漂移。')
    lines += ['', '## 说明', ''] + [f'- {x}' for x in r['notes']]
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser(description='检查 STM32CubeMX .ioc 与源码资源一致性')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--ioc')
    ap.add_argument('--output', '-o', help='JSON 输出')
    ap.add_argument('--report', help='Markdown 报告')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--fail-on-high', action='store_true')
    args = ap.parse_args()

    root = find_project_root(args.project)
    result = audit(root, Path(args.ioc).resolve() if args.ioc else None)
    if args.output:
        write_json(Path(args.output), result)
    if args.report:
        p = Path(args.report); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(render_md(result), encoding='utf-8')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not args.output:
        print(render_md(result))
    if args.fail_on_high and (result['summary']['critical'] or result['summary']['high']):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
