#!/usr/bin/env python3
"""FreeRTOS 运行时 Task/Stack/Heap 日志分析器。"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TASK_PREFIX = '@FREERTOS_TASK'
SNAP_PREFIX = '@FREERTOS_SNAPSHOT'


def parse_payload(rest: str) -> dict[str, Any] | None:
    rest = rest.strip()
    if not rest:
        return {}
    if rest.startswith('{'):
        try:
            return json.loads(rest)
        except json.JSONDecodeError:
            return None
    out: dict[str, Any] = {}
    for key, val in re.findall(r'(\w+)=((?:"[^"]*")|\S+)', rest):
        val = val.strip('"')
        if re.fullmatch(r'-?\d+', val):
            out[key] = int(val)
        elif re.fullmatch(r'0x[0-9A-Fa-f]+', val):
            out[key] = int(val, 16)
        else:
            out[key] = val
    return out


def parse_log(text: str) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    malformed = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if TASK_PREFIX in s:
            rest = s.split(TASK_PREFIX, 1)[1]
            row = parse_payload(rest)
            if row is None:
                malformed.append({'line': i, 'text': s})
            else:
                row['_line'] = i
                tasks.append(row)
        elif SNAP_PREFIX in s:
            rest = s.split(SNAP_PREFIX, 1)[1]
            row = parse_payload(rest)
            if row is None:
                malformed.append({'line': i, 'text': s})
            else:
                row['_line'] = i
                snapshots.append(row)
    return {'snapshots': snapshots, 'tasks': tasks, 'malformed': malformed}


def analyze(parsed: dict[str, Any], warn_words: int, critical_words: int, heap_warn_bytes: int | None, stack_word_bytes: int) -> dict[str, Any]:
    tasks = parsed['tasks']
    findings = []
    latest_by_name: dict[str, dict[str, Any]] = {}
    for t in tasks:
        name = str(t.get('name', '?'))
        latest_by_name[name] = t
        hwm = t.get('stack_hwm_words')
        if isinstance(hwm, int):
            if hwm <= critical_words:
                findings.append({'severity': 'critical', 'type': 'low_stack_margin', 'task': name, 'stack_hwm_words': hwm,
                                 'message': f'任务 {name} 最小剩余栈仅 {hwm} words（约 {hwm * stack_word_bytes} B）'})
            elif hwm <= warn_words:
                findings.append({'severity': 'high', 'type': 'low_stack_margin', 'task': name, 'stack_hwm_words': hwm,
                                 'message': f'任务 {name} 栈余量偏低：{hwm} words（约 {hwm * stack_word_bytes} B）'})

    snapshots = parsed['snapshots']
    latest_snapshot = snapshots[-1] if snapshots else None
    if latest_snapshot and heap_warn_bytes is not None:
        free_heap = latest_snapshot.get('free_heap')
        if isinstance(free_heap, int) and free_heap <= heap_warn_bytes:
            findings.append({'severity': 'high', 'type': 'low_heap', 'free_heap': free_heap,
                             'message': f'FreeRTOS 剩余 Heap 仅 {free_heap} B'})

    runtime_total = sum(int(t.get('runtime_counter', 0) or 0) for t in latest_by_name.values())
    latest_tasks = []
    for name, t in sorted(latest_by_name.items()):
        row = dict(t)
        rc = int(row.get('runtime_counter', 0) or 0)
        if runtime_total > 0:
            row['runtime_percent'] = round(rc * 100.0 / runtime_total, 2)
        hwm = row.get('stack_hwm_words')
        if isinstance(hwm, int):
            row['stack_hwm_bytes_est'] = hwm * stack_word_bytes
        latest_tasks.append(row)

    return {
        'snapshot_count': len(snapshots),
        'task_record_count': len(tasks),
        'latest_snapshot': latest_snapshot,
        'latest_tasks': latest_tasks,
        'malformed': parsed['malformed'],
        'findings': findings,
        'summary': {
            'task_count': len(latest_tasks),
            'critical': sum(1 for f in findings if f['severity'] == 'critical'),
            'high': sum(1 for f in findings if f['severity'] == 'high'),
        },
        'notes': [
            'stack_hwm_words 是 FreeRTOS High Water Mark，表示历史最少剩余栈深度，不是当前瞬时已用栈。',
            f'本次按 StackType_t={stack_word_bytes} bytes 估算字节；请按目标架构确认。',
        ],
    }


def render_markdown(r: dict[str, Any]) -> str:
    lines = ['# FreeRTOS 运行时 Task/Stack 报告', '',
             f"- Task 数：**{r['summary']['task_count']}**",
             f"- 快照数：**{r['snapshot_count']}**",
             f"- Critical：**{r['summary']['critical']}**",
             f"- High：**{r['summary']['high']}**", '']
    if r.get('latest_snapshot'):
        lines += ['## 最新系统快照', '']
        for k, v in r['latest_snapshot'].items():
            if not k.startswith('_'):
                lines.append(f'- `{k}` = `{v}`')
        lines.append('')

    lines += ['## Task', '', '| Task | 状态 | 优先级 | Stack HWM (words) | 估算余量(B) | Runtime % |',
              '|---|---:|---:|---:|---:|---:|']
    for t in r['latest_tasks']:
        lines.append(f"| {t.get('name','?')} | {t.get('state','?')} | {t.get('priority','?')} | {t.get('stack_hwm_words','?')} | {t.get('stack_hwm_bytes_est','?')} | {t.get('runtime_percent','?')} |")
    if not r['latest_tasks']:
        lines.append('| _无记录_ | | | | | |')

    lines += ['', '## 风险', '']
    if r['findings']:
        for f in r['findings']:
            lines.append(f"- **{f['severity'].upper()}** `{f['type']}`：{f['message']}")
    else:
        lines.append('未命中配置阈值。')
    lines += ['', '## 说明', ''] + [f'- {x}' for x in r['notes']]
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser(description='FreeRTOS Task/Stack/Heap 运行时日志分析')
    ap.add_argument('log')
    ap.add_argument('--stack-warn-words', type=int, default=64)
    ap.add_argument('--stack-critical-words', type=int, default=24)
    ap.add_argument('--stack-word-bytes', type=int, default=4)
    ap.add_argument('--heap-warn-bytes', type=int)
    ap.add_argument('--json-out')
    ap.add_argument('--report')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    p = Path(args.log)
    if not p.exists():
        ap.error(f'日志不存在：{p}')
    parsed = parse_log(p.read_text(encoding='utf-8', errors='replace'))
    result = analyze(parsed, args.stack_warn_words, args.stack_critical_words, args.heap_warn_bytes, args.stack_word_bytes)
    result['log'] = str(p.resolve())

    if args.json_out:
        out = Path(args.json_out); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.report:
        out = Path(args.report); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(result), encoding='utf-8')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))


if __name__ == '__main__':
    main()
