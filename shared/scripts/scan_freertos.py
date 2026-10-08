#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import find_functions, find_project_root, iter_source_files, norm_rel, read_text, write_json

TASK_ATTR_RE = re.compile(r'const\s+osThreadAttr_t\s+(\w+)\s*=\s*\{(.*?)\};', re.S)
TASK_NEW_RE = re.compile(r'(\w+)\s*=\s*osThreadNew\s*\(\s*(\w+)\s*,\s*([^,]+),\s*&?(\w+|NULL)\s*\)')
XTASK_RE = re.compile(r'xTaskCreate(?:Static)?\s*\(\s*(\w+)\s*,\s*"([^"]+)"\s*,\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*&?(\w+|NULL)')
OBJ_PATTERNS = {
    'queue': [
        re.compile(r'(\w+)\s*=\s*osMessageQueueNew\s*\(\s*([^,]+),\s*([^,]+),'),
        re.compile(r'(\w+)\s*=\s*xQueueCreate\s*\(\s*([^,]+),\s*([^\)]+)\)'),
    ],
    'mutex': [
        re.compile(r'(\w+)\s*=\s*osMutexNew\s*\('),
        re.compile(r'(\w+)\s*=\s*xSemaphoreCreateMutex(?:Static)?\s*\('),
    ],
    'semaphore': [
        re.compile(r'(\w+)\s*=\s*osSemaphoreNew\s*\(\s*([^,]+),\s*([^,]+),'),
        re.compile(r'(\w+)\s*=\s*xSemaphoreCreate(?:Binary|Counting)(?:Static)?\s*\('),
    ],
    'event_flags': [
        re.compile(r'(\w+)\s*=\s*osEventFlagsNew\s*\('),
        re.compile(r'(\w+)\s*=\s*xEventGroupCreate(?:Static)?\s*\('),
    ],
    'timer': [
        re.compile(r'(\w+)\s*=\s*osTimerNew\s*\('),
        re.compile(r'(\w+)\s*=\s*xTimerCreate(?:Static)?\s*\('),
    ],
}

CALL_RE = re.compile(r'\b([A-Za-z_]\w*)\s*\(')
RTOS_API_RE = re.compile(r'\b(os(?:Thread|MessageQueue|Semaphore|Mutex|EventFlags|Timer|Delay|Kernel)\w*|x(?:Queue|Semaphore|EventGroup|Task|Timer)\w*|vTask\w*|ulTask\w*)\s*\(')
ISR_NAME_RE = re.compile(r'(IRQHandler|Callback)$')


def parse_attr(body: str) -> dict:
    out = {}
    for field in ('name', 'stack_size', 'priority', 'attr_bits', 'cb_size'):
        m = re.search(r'\.' + re.escape(field) + r'\s*=\s*([^,\n}]+)', body)
        if m:
            out[field] = m.group(1).strip().strip('"')
    return out


def scan_freertos(root: Path) -> dict:
    files = list(iter_source_files(root, include_generated=True))
    attrs = {}
    tasks = []
    objects = []
    functions_by_file = []
    isr_rtos_calls = []

    for path in files:
        text = read_text(path)
        rel = norm_rel(path, root)
        for m in TASK_ATTR_RE.finditer(text):
            attrs[m.group(1)] = parse_attr(m.group(2))

        for m in TASK_NEW_RE.finditer(text):
            handle, entry, param, attr_name = m.groups()
            tasks.append({
                'api': 'CMSIS-RTOS2', 'handle': handle, 'entry': entry, 'parameter': param.strip(),
                'attributes': attrs.get(attr_name, {}), 'attr_symbol': attr_name, 'file': rel,
            })
        for m in XTASK_RE.finditer(text):
            entry, name, stack, param, priority, handle = m.groups()
            tasks.append({
                'api': 'FreeRTOS', 'handle': handle, 'entry': entry, 'name': name,
                'stack_size': stack.strip(), 'priority': priority.strip(), 'parameter': param.strip(), 'file': rel,
            })

        for kind, patterns in OBJ_PATTERNS.items():
            for pat in patterns:
                for m in pat.finditer(text):
                    row = {'kind': kind, 'handle': m.group(1), 'file': rel, 'api': 'CMSIS/FreeRTOS'}
                    if kind == 'queue' and len(m.groups()) >= 3:
                        row['count'] = m.group(2).strip()
                        row['item_size'] = m.group(3).strip()
                    elif kind == 'semaphore' and len(m.groups()) >= 3:
                        row['max_count'] = m.group(2).strip()
                        row['initial_count'] = m.group(3).strip()
                    objects.append(row)

        for fn in find_functions(text):
            body = fn['body']
            calls = sorted(set(CALL_RE.findall(body)))
            rtos_calls = sorted(set(RTOS_API_RE.findall(body)))
            row = {'name': fn['name'], 'file': rel, 'calls': calls, 'rtos_calls': rtos_calls}
            functions_by_file.append(row)
            if ISR_NAME_RE.search(fn['name']) and rtos_calls:
                unsafe = [c for c in rtos_calls if c.startswith('x') and not c.endswith('FromISR')]
                # CMSIS-RTOS2 allows selected ISR-safe calls only with timeout=0; flag for review, not automatic failure.
                isr_rtos_calls.append({'function': fn['name'], 'file': rel, 'calls': rtos_calls, 'possibly_unsafe': unsafe})

    # Enrich tasks with entry function call summaries.
    fn_index = {(f['file'], f['name']): f for f in functions_by_file}
    by_name = {}
    for f in functions_by_file:
        by_name.setdefault(f['name'], []).append(f)
    for task in tasks:
        candidates = by_name.get(task['entry'], [])
        if candidates:
            f = candidates[0]
            task['entry_file'] = f['file']
            task['calls'] = f['calls']
            task['rtos_calls'] = f['rtos_calls']

    cfg = {}
    cfg_files = list(root.rglob('FreeRTOSConfig.h'))
    if cfg_files:
        text = read_text(cfg_files[0])
        for name in ('configMAX_PRIORITIES', 'configTOTAL_HEAP_SIZE', 'configTICK_RATE_HZ', 'configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY', 'configMAX_SYSCALL_INTERRUPT_PRIORITY'):
            m = re.search(r'^\s*#define\s+' + name + r'\s+(.+)$', text, re.M)
            if m:
                cfg[name] = m.group(1).strip()
        cfg['file'] = norm_rel(cfg_files[0], root)

    return {
        'project': str(root),
        'tasks': tasks,
        'objects': objects,
        'isr_rtos_calls': isr_rtos_calls,
        'freertos_config': cfg,
        'summary': {
            'task_count': len(tasks),
            'queue_count': sum(1 for x in objects if x['kind'] == 'queue'),
            'mutex_count': sum(1 for x in objects if x['kind'] == 'mutex'),
            'semaphore_count': sum(1 for x in objects if x['kind'] == 'semaphore'),
            'event_flags_count': sum(1 for x in objects if x['kind'] == 'event_flags'),
            'timer_count': sum(1 for x in objects if x['kind'] == 'timer'),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description='Scan CMSIS-RTOS2/FreeRTOS tasks and IPC objects')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--output', '-o')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    root = find_project_root(args.project)
    data = scan_freertos(root)
    if args.output:
        write_json(Path(args.output), data)
    elif args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        s = data['summary']
        print(f"Tasks={s['task_count']} Queues={s['queue_count']} Mutexes={s['mutex_count']} Semaphores={s['semaphore_count']} Events={s['event_flags_count']} Timers={s['timer_count']}")
        for t in data['tasks']:
            print(f"- {t.get('name') or t.get('handle')}: {t['entry']} stack={t.get('stack_size') or t.get('attributes', {}).get('stack_size')} priority={t.get('priority') or t.get('attributes', {}).get('priority')}")


if __name__ == '__main__':
    main()
