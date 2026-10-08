#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from _common import find_functions, find_project_root, iter_source_files, norm_rel, read_text, write_json
from parse_ioc import discover_ioc, parse_ioc_file

NVIC_SRC_RE = re.compile(r'HAL_NVIC_SetPriority\s*\(\s*([A-Za-z0-9_]+_IRQn)\s*,\s*([^,\)]+)\s*,\s*([^\)]+)\)')
DMA_LINK_RE = re.compile(r'__HAL_LINKDMA\s*\(\s*([^,]+),\s*([^,]+),\s*([^\)]+)\)')
DMA_HANDLE_RE = re.compile(r'\bDMA_HandleTypeDef\s+(\w+)\s*;')
IRQ_FN_RE = re.compile(r'([A-Za-z0-9_]+)_IRQHandler$')
RTOS_ISR_API_RE = re.compile(r'\b(os(?:ThreadFlagsSet|EventFlagsSet|MessageQueuePut|SemaphoreRelease)|x(?:Queue|Semaphore|EventGroup)\w*FromISR|vTaskNotifyGiveFromISR|xTaskNotify\w*FromISR)\s*\(')
UNSAFE_ISR_RE = re.compile(r'\b(HAL_Delay|osDelay|vTaskDelay|printf|sprintf|snprintf|f_(?:open|write|read|close|sync|rename|unlink)|malloc|free|strtok|sscanf)\s*\(')


def parse_int_expr(expr: str) -> int | None:
    expr = expr.strip()
    try:
        return int(expr, 0)
    except ValueError:
        m = re.search(r'(\d+)', expr)
        return int(m.group(1)) if m else None


def extract_max_syscall_priority(root: Path) -> int | None:
    cfgs = list(root.rglob('FreeRTOSConfig.h'))
    if not cfgs:
        return None
    text = read_text(cfgs[0])
    m = re.search(r'^\s*#define\s+configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY\s+([^\n/]+)', text, re.M)
    return parse_int_expr(m.group(1)) if m else None


def audit(root: Path, ioc_path: Path | None = None) -> dict:
    findings = []
    resources = {'pins': [], 'dma': [], 'irqs': []}
    ioc_data = None
    if ioc_path is None:
        ioc_path = discover_ioc(root)
    if ioc_path and ioc_path.exists():
        ioc_data = parse_ioc_file(ioc_path)
        resources['pins'] = ioc_data['pins']
        resources['dma'] = ioc_data['dma']
        resources['irqs'].extend(ioc_data['nvic'])

        # Duplicate labels are a common board-resource ambiguity.
        labels = defaultdict(list)
        for p in ioc_data['pins']:
            if p.get('label'):
                labels[p['label']].append(p['pin'])
        for label, pins in labels.items():
            if len(pins) > 1:
                findings.append({
                    'severity': 'medium', 'type': 'duplicate_gpio_label',
                    'message': f'GPIO label {label} is used by multiple pins: {pins}', 'pins': pins,
                })

        # Detect suspicious reuse of debug pins when SWD/JTAG is enabled.
        debug_signals = {p['pin']: p.get('signal') for p in ioc_data['pins'] if (p.get('signal') or '').startswith('SYS_')}
        for p in ioc_data['pins']:
            if p['pin'] in {'PA13', 'PA14', 'PA15', 'PB3', 'PB4'} and p.get('signal') and not (p.get('signal') or '').startswith('SYS_'):
                findings.append({
                    'severity': 'low', 'type': 'debug_pin_reuse', 'pin': p['pin'], 'signal': p.get('signal'),
                    'message': f"{p['pin']} is commonly used by SWD/JTAG; verify debug configuration before reusing it",
                })

    source_irq_priority = {}
    irq_rtos_usage = defaultdict(list)
    dma_handles = defaultdict(list)
    dma_links = []
    unsafe_isr = []

    for path in iter_source_files(root, include_generated=True):
        rel = norm_rel(path, root)
        text = read_text(path)
        for m in NVIC_SRC_RE.finditer(text):
            irq, prio_expr, sub_expr = m.groups()
            prio = parse_int_expr(prio_expr)
            source_irq_priority[irq] = {'priority': prio, 'sub_priority': parse_int_expr(sub_expr), 'file': rel}
        for m in DMA_HANDLE_RE.finditer(text):
            dma_handles[m.group(1)].append(rel)
        for m in DMA_LINK_RE.finditer(text):
            dma_links.append({'owner': m.group(1).strip(), 'field': m.group(2).strip(), 'dma_handle': m.group(3).strip(), 'file': rel})
        for fn in find_functions(text):
            if not (fn['name'].endswith('IRQHandler') or fn['name'].endswith('Callback')):
                continue
            for api in RTOS_ISR_API_RE.findall(fn['body']):
                irq_rtos_usage[fn['name']].append({'api': api, 'file': rel})
            bad = sorted(set(UNSAFE_ISR_RE.findall(fn['body'])))
            if bad:
                unsafe_isr.append({'function': fn['name'], 'file': rel, 'calls': bad})
                findings.append({
                    'severity': 'high', 'type': 'unsafe_isr_work', 'function': fn['name'], 'file': rel, 'calls': bad,
                    'message': f"ISR/callback contains blocking or heavy calls: {', '.join(bad)}",
                })

    max_syscall = extract_max_syscall_priority(root)
    for fn_name, uses in irq_rtos_usage.items():
        m = IRQ_FN_RE.match(fn_name)
        if not m:
            # HAL callbacks cannot be reliably mapped to an IRQ statically; report as review item.
            findings.append({
                'severity': 'low', 'type': 'callback_rtos_priority_review', 'function': fn_name, 'uses': uses,
                'message': 'HAL callback uses RTOS ISR-safe API; verify every possible calling IRQ priority against configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY',
            })
            continue
        irq = m.group(1) + '_IRQn'
        cfg = source_irq_priority.get(irq)
        if cfg and cfg['priority'] is not None and max_syscall is not None and cfg['priority'] < max_syscall:
            findings.append({
                'severity': 'critical', 'type': 'freertos_irq_priority_violation',
                'irq': irq, 'priority': cfg['priority'], 'max_syscall_priority': max_syscall,
                'function': fn_name, 'uses': uses,
                'message': f"{irq} priority {cfg['priority']} is numerically higher than FreeRTOS syscall threshold {max_syscall}",
            })

    # Duplicate DMA handle declarations are usually harmless extern/definition mixes, but multiple source definitions are suspicious.
    for handle, files in dma_handles.items():
        unique = sorted(set(files))
        if len(unique) > 1:
            findings.append({
                'severity': 'low', 'type': 'dma_handle_multi_decl', 'handle': handle, 'files': unique,
                'message': f'DMA handle {handle} appears in multiple translation units; verify there is exactly one definition',
            })

    # Same DMA handle linked to multiple owner fields can be intentional, but often indicates a collision.
    by_dma = defaultdict(list)
    for link in dma_links:
        by_dma[link['dma_handle']].append(link)
    for handle, links in by_dma.items():
        owners = {(x['owner'], x['field']) for x in links}
        if len(owners) > 1:
            findings.append({
                'severity': 'medium', 'type': 'dma_shared_handle', 'dma_handle': handle, 'links': links,
                'message': f'DMA handle {handle} is linked to multiple peripheral fields; verify sharing is intentional and mutually exclusive',
            })

    resources['irqs_source'] = source_irq_priority
    resources['dma_links'] = dma_links
    return {
        'project': str(root),
        'ioc_file': str(ioc_path) if ioc_path else None,
        'freertos_max_syscall_priority': max_syscall,
        'resources': resources,
        'findings': findings,
        'summary': {
            'critical': sum(1 for f in findings if f['severity'] == 'critical'),
            'high': sum(1 for f in findings if f['severity'] == 'high'),
            'medium': sum(1 for f in findings if f['severity'] == 'medium'),
            'low': sum(1 for f in findings if f['severity'] == 'low'),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description='Audit STM32 pin/DMA/IRQ and FreeRTOS interrupt safety')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--ioc')
    ap.add_argument('--output', '-o')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--fail-on-critical', action='store_true')
    args = ap.parse_args()
    root = find_project_root(args.project)
    data = audit(root, Path(args.ioc).resolve() if args.ioc else None)
    if args.output:
        write_json(Path(args.output), data)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif not args.output:
        s = data['summary']
        print(f"critical={s['critical']} high={s['high']} medium={s['medium']} low={s['low']}")
        for f in data['findings'][:50]:
            print(f"[{f['severity'].upper()}] {f['type']}: {f['message']}")
    if args.fail_on_critical and data['summary']['critical']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
