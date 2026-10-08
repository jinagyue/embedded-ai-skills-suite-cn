#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import classify_layer, find_project_root, iter_source_files, norm_rel, read_text, write_json

HAL_PATTERNS = [
    (re.compile(r'\bHAL_[A-Za-z0-9_]+\b'), 'HAL API'),
    (re.compile(r'\bLL_[A-Za-z0-9_]+\b'), 'LL API'),
    (re.compile(r'\bh(?:uart|spi|i2c|adc|tim|dma|can|fdcan|rtc|sd|rng)\d+\b', re.I), 'HAL handle'),
    (re.compile(r'\bGPIO[A-K]\b|\bGPIO_PIN_\d+\b'), 'GPIO symbol'),
    (re.compile(r'\b__HAL_[A-Za-z0-9_]+\b'), 'HAL macro'),
]
OS_PATTERNS = [
    re.compile(r'\bos(?:Thread|MessageQueue|Semaphore|Mutex|EventFlags|Timer|Delay|Kernel)\w*\b'),
    re.compile(r'\b(?:xQueue|xSemaphore|xEventGroup|xTask|vTask|ulTask|xTimer)\w*\b'),
]

DEFAULT_ALLOWED_HAL = {'vendor', 'bsp_driver', 'platform'}
DEFAULT_ALLOWED_OS = {'rtos', 'platform'}


def scan(root: Path, strict_osal: bool = False) -> dict:
    findings = []
    counts = {}
    for path in iter_source_files(root, include_generated=False):
        rel = norm_rel(path, root)
        layer = classify_layer(rel)
        text = read_text(path)
        if not text:
            continue
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            if line.lstrip().startswith('//'):
                continue
            for pat, name in HAL_PATTERNS:
                for m in pat.finditer(line):
                    if layer not in DEFAULT_ALLOWED_HAL:
                        severity = 'high' if layer in {'app', 'service', 'protocol'} else 'medium'
                        findings.append({
                            'severity': severity,
                            'type': 'hal_leak',
                            'file': rel,
                            'line': idx,
                            'layer': layer,
                            'symbol': m.group(0),
                            'category': name,
                            'message': f'{name} leaked into {layer} layer',
                        })
                        counts[layer] = counts.get(layer, 0) + 1
            if strict_osal:
                for pat in OS_PATTERNS:
                    for m in pat.finditer(line):
                        if layer not in DEFAULT_ALLOWED_OS:
                            severity = 'high' if layer in {'app', 'device', 'protocol'} else 'medium'
                            findings.append({
                                'severity': severity,
                                'type': 'os_leak',
                                'file': rel,
                                'line': idx,
                                'layer': layer,
                                'symbol': m.group(0),
                                'message': f'RTOS API leaked into {layer}; prefer RTOS/OSAL or platform port',
                            })
                            counts[layer] = counts.get(layer, 0) + 1
    return {'project': str(root), 'strict_osal': strict_osal, 'findings': findings, 'counts_by_layer': counts}


def main() -> None:
    ap = argparse.ArgumentParser(description='Detect HAL/LL/RTOS leakage across architecture layers')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--strict-osal', action='store_true', help='also flag direct RTOS API outside RTOS/Platform')
    ap.add_argument('--output', '-o')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--fail-on-high', action='store_true')
    args = ap.parse_args()
    root = find_project_root(args.project)
    data = scan(root, args.strict_osal)
    if args.output:
        write_json(Path(args.output), data)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif not args.output:
        print(f"Findings: {len(data['findings'])}")
        for f in data['findings'][:50]:
            print(f"[{f['severity'].upper()}] {f['file']}:{f['line']} {f['symbol']} - {f['message']}")
    if args.fail_on_high and any(f['severity'] == 'high' for f in data['findings']):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
