from pathlib import Path
import json
import os
import subprocess
import sys

os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'shared' / 'scripts'
PROJ = ROOT / 'tests' / 'fixtures' / 'sample_project'
RUNTIME = ROOT / 'tests' / 'fixtures' / 'runtime'
OUT = ROOT / 'tests' / '_out'
OUT.mkdir(exist_ok=True)


def run(name, *args):
    cmd = [sys.executable, str(SCRIPTS / name), str(PROJ), *args]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print('FAILED', cmd)
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    return p


# V0.3 基础链路
run('parse_ioc.py', '--output', str(OUT / 'ioc.json'))
run('scan_freertos.py', '--output', str(OUT / 'rtos.json'))
run('include_graph.py', '--output', str(OUT / 'includes.json'), '--mermaid', str(OUT / 'includes.mmd'))
run('hal_leak_check.py', '--output', str(OUT / 'leaks.json'))
run('stm32_resource_audit.py', '--output', str(OUT / 'resources.json'))
run('analyze_project.py', '--output', str(OUT / 'model.json'))
run('generate_arch_docs.py', '--output-dir', str(OUT / 'reports'))

# V0.4：IOC/source 一致性
run('ioc_source_consistency.py', '--output', str(OUT / 'ioc_consistency.json'), '--report', str(OUT / 'IOC_SOURCE_CONSISTENCY.md'))

# 自动调试静态模式（会同时运行一致性检查）
subprocess.run([sys.executable, str(SCRIPTS / 'auto_debug.py'), 'static', '--workspace', str(PROJ)], check=True)

TOOLS = ROOT / 'tools'
arch_map = TOOLS / 'architecture_checker' / 'arch-map.example.json'
arch_out = OUT / 'architecture_gate.json'
pa = subprocess.run([sys.executable, str(TOOLS / 'architecture_checker' / 'architecture_checker.py'), str(PROJ), '--map', str(arch_map), '--json-out', str(arch_out)], capture_output=True, text=True)
if pa.returncode != 0:
    print(pa.stdout, pa.stderr)
    raise SystemExit(pa.returncode)
subprocess.run([sys.executable, str(TOOLS / 'skill_validator.py'), str(ROOT)], check=True)

# V0.4：Keil map
subprocess.run([
    sys.executable, str(TOOLS / 'keil_map_analyzer' / 'keil_map_analyzer.py'),
    str(PROJ / 'build' / 'sample.map'),
    '--json-out', str(OUT / 'keil_map.json'), '--report', str(OUT / 'KEIL_MAP_REPORT.md')
], check=True)

# V0.4：HardFault 解码（不依赖 addr2line 工具链也能完成寄存器解码）
subprocess.run([
    sys.executable, str(TOOLS / 'hardfault_decoder' / 'hardfault_decoder.py'),
    '--log', str(RUNTIME / 'hardfault.log'),
    '--json-out', str(OUT / 'hardfault.json'), '--report', str(OUT / 'HARDFAULT_REPORT.md')
], check=True)

# V0.4：FreeRTOS runtime
subprocess.run([
    sys.executable, str(TOOLS / 'freertos_runtime' / 'freertos_runtime_analyzer.py'),
    str(RUNTIME / 'freertos.log'),
    '--json-out', str(OUT / 'freertos_runtime.json'), '--report', str(OUT / 'FREERTOS_RUNTIME.md')
], check=True)

# V0.4：addr2line wrapper 的“工具缺失容错”路径；伪 ELF 仅验证工具发现/输入处理，不执行解析。
fake_elf = OUT / 'fake.elf'
fake_elf.write_bytes(b'not-an-elf')
subprocess.run([
    sys.executable, str(TOOLS / 'addr2line_resolver' / 'addr2line_resolver.py'),
    '--elf', str(fake_elf), '0x08000001', '--tool', '__definitely_missing_addr2line__',
    '--allow-missing-tool', '--json-out', str(OUT / 'addr2line_missing.json')
], check=True)

# V0.4：完整 cycle 编排（不烧录），验证 MAP + Observe + FreeRTOS + HardFault 自动串联。
config_dir = PROJ / '.embedded-ai'
config_dir.mkdir(exist_ok=True)
emitter = RUNTIME / 'emit_runtime.py'
config = {
    'schema_version': '0.4',
    'analysis': {'strict_osal': False},
    'commands': {
        'build': f'"{sys.executable}" "{emitter}" build',
        'test': None,
        'flash': None,
        'observe': f'"{sys.executable}" "{emitter}"',
    },
    'serial': {'port': None, 'baud': 115200, 'duration_s': 5, 'mode': 'both'},
    'freertos_runtime': {'stack_warn_words': 64, 'stack_critical_words': 24, 'stack_word_bytes': 4, 'heap_warn_bytes': 5000},
    'auto_debug': {
        'analyze_elf': True, 'analyze_map': True, 'check_ioc_consistency': True,
        'decode_hardfault': True, 'analyze_freertos_runtime': True,
        'addr2line_tool': None, 'allow_flash': False, 'external_embeddedskills_root': None,
    },
}
(config_dir / 'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
cycle = subprocess.run([
    sys.executable, str(SCRIPTS / 'auto_debug.py'), 'cycle', '--workspace', str(PROJ), '--json'
], capture_output=True, text=True, check=True)
cycle_result = json.loads(cycle.stdout)
cycle_actions = {a.get('name') for a in cycle_result['actions']}
assert {'ioc-source-consistency', 'build', 'keil-map-analysis', 'observe', 'freertos-runtime-analysis', 'hardfault-decode'} <= cycle_actions
assert cycle_result['safe_flash_default'] is True

# Assertions

ioc = json.loads((OUT / 'ioc.json').read_text())
assert ioc['mcu']['name'] == 'STM32F405RGTx'
rtos = json.loads((OUT / 'rtos.json').read_text())
assert rtos['summary']['task_count'] >= 1
leaks = json.loads((OUT / 'leaks.json').read_text())
assert any(f['type'] == 'hal_leak' for f in leaks['findings'])
resources = json.loads((OUT / 'resources.json').read_text())
assert any(f['type'] == 'freertos_irq_priority_violation' for f in resources['findings'])
assert (OUT / 'reports' / 'ARCHITECTURE.md').exists()
arch = json.loads(arch_out.read_text())
assert any(f['type'] == 'hal_api_leak' for f in arch['findings'])

consistency = json.loads((OUT / 'ioc_consistency.json').read_text())
assert any(f['type'] == 'nvic_priority_mismatch' for f in consistency['findings'])

m = json.loads((OUT / 'keil_map.json').read_text())
assert m['program_size']['estimated_flash_bytes'] == 45000 + 2800 + 640
assert m['largest_functions'][0]['name'] == 'BigFilter'

hf = json.loads((OUT / 'hardfault.json').read_text())
assert any(x['name'] == 'PRECISERR' for x in hf['cfsr_flags'])
assert any(x['name'] == 'BFARVALID' for x in hf['cfsr_flags'])
assert hf['exc_return']['stack_used'] == 'PSP'

fr = json.loads((OUT / 'freertos_runtime.json').read_text())
assert fr['summary']['task_count'] == 3
assert any(f['severity'] == 'critical' and f['task'] == 'comm' for f in fr['findings'])

addr = json.loads((OUT / 'addr2line_missing.json').read_text())
assert addr['status'] == 'tool_missing'

print('smoke tests: OK')
