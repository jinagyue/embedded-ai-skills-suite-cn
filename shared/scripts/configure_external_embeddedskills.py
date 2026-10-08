#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import find_project_root, load_json, norm_rel, write_json
from parse_ioc import discover_ioc, parse_ioc_file

OPENOCD_TARGETS = {
    'F0': 'target/stm32f0x.cfg',
    'F1': 'target/stm32f1x.cfg',
    'F2': 'target/stm32f2x.cfg',
    'F3': 'target/stm32f3x.cfg',
    'F4': 'target/stm32f4x.cfg',
    'F7': 'target/stm32f7x.cfg',
    'G0': 'target/stm32g0x.cfg',
    'G4': 'target/stm32g4x.cfg',
    'H7': 'target/stm32h7x.cfg',
    'L0': 'target/stm32l0.cfg',
    'L1': 'target/stm32l1.cfg',
    'L4': 'target/stm32l4x.cfg',
    'L5': 'target/stm32l5x.cfg',
    'U5': 'target/stm32u5x.cfg',
    'WB': 'target/stm32wbx.cfg',
    'WL': 'target/stm32wlx.cfg',
}


def compact_device(name: str | None) -> str | None:
    if not name:
        return None
    m = re.match(r'^(STM32[A-Z]\d{3}[A-Z0-9]{2})', name.upper())
    return m.group(1) if m else name.replace('Tx', '').replace('Ux', '').replace('Yx', '')


def family_code(name: str | None, family: str | None) -> str | None:
    src = (name or family or '').upper()
    m = re.search(r'STM32([A-Z]\d|WB|WL)', src)
    if m:
        return m.group(1)
    m = re.search(r'\b(F0|F1|F2|F3|F4|F7|G0|G4|H7|L0|L1|L4|L5|U5|WB|WL)\b', src)
    return m.group(1) if m else None


def generate(root: Path, probe: str = 'stlink') -> dict:
    ioc_path = discover_ioc(root)
    ioc = parse_ioc_file(ioc_path) if ioc_path else {}
    mcu = ioc.get('mcu') or {}
    dev = compact_device(mcu.get('name'))
    fam = family_code(mcu.get('name'), mcu.get('family'))
    target = OPENOCD_TARGETS.get(fam or '')

    cfg = {
        'workflow': {
            'preferred_build': 'auto',
            'preferred_flash': 'auto',
            'preferred_debug': 'auto',
            'preferred_observe': 'auto',
        }
    }
    keil = sorted(root.rglob('*.uvprojx'))
    if len(keil) == 1:
        cfg['keil'] = {'project': norm_rel(keil[0], root)}

    if dev:
        cfg['jlink'] = {'device': dev, 'interface': 'SWD', 'speed': 4000}
        cfg['probe-rs'] = {'chip': dev, 'protocol': 'swd'}
    if target:
        interface = 'interface/stlink.cfg' if probe == 'stlink' else 'interface/cmsis-dap.cfg'
        cfg['openocd'] = {'interface': interface, 'target': target}
    cfg['_generated'] = {
        'warning': 'Generated heuristically. Verify device/chip/OpenOCD target against your installed debugger and MCU.',
        'ioc': str(ioc_path) if ioc_path else None,
        'mcu': mcu.get('name'),
    }
    return cfg


def deep_merge(base: dict, new: dict) -> dict:
    out = dict(base)
    for k, v in new.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description='Generate zhinkgit/embeddedskills compatible .embeddedskills/config.json')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--probe', choices=['stlink', 'cmsis-dap'], default='stlink')
    ap.add_argument('--output')
    ap.add_argument('--force', action='store_true', help='replace existing config instead of merging')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    root = find_project_root(args.project)
    path = Path(args.output).resolve() if args.output else root / '.embeddedskills' / 'config.json'
    new = generate(root, args.probe)
    if path.exists() and not args.force:
        data = deep_merge(load_json(path, {}), new)
    else:
        data = new
    write_json(path, data)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f'Wrote {path}')
        print('Verify generated debugger device/target before flashing.')


if __name__ == '__main__':
    main()
