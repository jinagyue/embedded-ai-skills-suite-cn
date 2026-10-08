#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

from _common import classify_layer, find_project_root, iter_source_files, norm_rel, write_json
from parse_ioc import discover_ioc, parse_ioc_file
from scan_freertos import scan_freertos
from include_graph import build_graph
from hal_leak_check import scan as scan_hal_leaks
from stm32_resource_audit import audit as audit_resources


def discover_build(root: Path) -> dict:
    keil = [norm_rel(p, root) for p in root.rglob('*.uvprojx')]
    cmake = [norm_rel(p, root) for p in root.rglob('CMakeLists.txt')]
    eide = [norm_rel(p, root) for p in root.rglob('eide.yml') if '.eide' in p.parts]
    make = [norm_rel(p, root) for p in root.rglob('Makefile')]
    return {'keil': sorted(keil), 'cmake': sorted(cmake), 'eide': sorted(eide), 'make': sorted(make)}


def discover_debug_tools() -> dict:
    names = {
        'jlink': ['JLinkExe', 'JLink.exe', 'JLinkGDBServerCLExe', 'JLinkGDBServerCL.exe'],
        'openocd': ['openocd'],
        'probe-rs': ['probe-rs'],
        'gdb': ['arm-none-eabi-gdb', 'gdb-multiarch'],
        'cmake': ['cmake'],
        'ninja': ['ninja'],
        'git': ['git'],
    }
    out = {}
    for k, candidates in names.items():
        found = None
        for c in candidates:
            found = shutil.which(c)
            if found:
                break
        out[k] = found
    try:
        import serial  # type: ignore
        out['pyserial'] = getattr(serial, '__version__', 'installed')
    except Exception:
        out['pyserial'] = None
    return out


def module_map(root: Path) -> dict:
    layers = defaultdict(list)
    for p in iter_source_files(root, include_generated=False):
        rel = norm_rel(p, root)
        layers[classify_layer(rel)].append(rel)
    return {k: sorted(v) for k, v in sorted(layers.items())}


def analyze(root: Path, strict_osal: bool = False) -> dict:
    ioc_path = discover_ioc(root)
    ioc = parse_ioc_file(ioc_path) if ioc_path else None
    rtos = scan_freertos(root)
    includes = build_graph(root, include_generated=False)
    leaks = scan_hal_leaks(root, strict_osal=strict_osal)
    resources = audit_resources(root, ioc_path)
    modules = module_map(root)
    build = discover_build(root)
    tools = discover_debug_tools()

    risk_score = 0
    risk_score += 10 * resources['summary']['critical']
    risk_score += 5 * resources['summary']['high']
    risk_score += 3 * len([x for x in leaks['findings'] if x['severity'] == 'high'])
    risk_score += 3 * len(includes['violations'])
    risk_score += 2 * len(rtos['isr_rtos_calls'])

    return {
        'schema_version': '0.2',
        'project': str(root),
        'ioc': ioc,
        'build': build,
        'debug_tools': tools,
        'modules': modules,
        'rtos': rtos,
        'include_graph': includes,
        'hal_leaks': leaks,
        'resource_audit': resources,
        'risk_score': risk_score,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description='One-shot STM32/FreeRTOS project analysis')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--strict-osal', action='store_true')
    ap.add_argument('--output', '-o', default=None)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    root = find_project_root(args.project)
    data = analyze(root, strict_osal=args.strict_osal)
    output = Path(args.output) if args.output else root / '.embedded-ai' / 'project_model.json'
    write_json(output, data)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        mcu = (data.get('ioc') or {}).get('mcu', {}).get('name') if data.get('ioc') else None
        print(f"Project: {root}")
        print(f"MCU: {mcu or 'unknown'}")
        print(f"Tasks: {data['rtos']['summary']['task_count']}, HAL leaks: {len(data['hal_leaks']['findings'])}, dependency violations: {len(data['include_graph']['violations'])}")
        print(f"Risk score: {data['risk_score']}")
        print(f"Model: {output}")


if __name__ == '__main__':
    main()
