#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from _common import find_project_root, write_json

PIN_RE = re.compile(r'^(P[A-K][0-9]{1,2}|P[A-K][0-9]{1,2}-.+|VP_.+?)\.(.+)$')


def parse_ioc_file(path: Path) -> dict:
    raw: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        raw[k.strip()] = v.strip()

    mcu = {
        'name': raw.get('Mcu.Name'),
        'family': raw.get('Mcu.Family'),
        'package': raw.get('Mcu.Package'),
        'user_name': raw.get('Mcu.UserName'),
        'core': raw.get('Mcu.CPN') or raw.get('Mcu.DeviceCPN'),
    }
    project = {
        'name': raw.get('ProjectManager.ProjectName'),
        'toolchain': raw.get('ProjectManager.ToolChain'),
        'firmware_package': raw.get('ProjectManager.FirmwarePackage'),
        'heap_size': raw.get('ProjectManager.HeapSize'),
        'stack_size': raw.get('ProjectManager.StackSize'),
    }

    ips = []
    for k, v in raw.items():
        if re.fullmatch(r'Mcu\.IP\d+', k):
            ips.append(v)
    ips = sorted(set(ips))

    pins: dict[str, dict[str, str]] = defaultdict(dict)
    virtual_pins: dict[str, dict[str, str]] = defaultdict(dict)
    for k, v in raw.items():
        m = PIN_RE.match(k)
        if not m:
            continue
        pin, field = m.groups()
        target = virtual_pins if pin.startswith('VP_') else pins
        target[pin][field] = v

    # Keep only useful pin data while preserving unrecognized fields.
    pin_rows = []
    for pin, cfg in sorted(pins.items()):
        pin_rows.append({
            'pin': pin,
            'signal': cfg.get('Signal'),
            'label': cfg.get('GPIO_Label'),
            'mode': cfg.get('Mode'),
            'locked': cfg.get('Locked'),
            'pull': cfg.get('GPIO_PuPd'),
            'speed': cfg.get('GPIO_Speed'),
            'output_level': cfg.get('GPIOParameters'),
            'raw': cfg,
        })

    dma = []
    for k, v in raw.items():
        lk = k.lower()
        if lk.startswith('dma.') or '.dma' in lk or lk.startswith('dmamux.'):
            dma.append({'key': k, 'value': v})

    nvic = []
    for k, v in raw.items():
        if k.startswith('NVIC.'):
            parts = [p.strip() for p in v.split(':')]
            # CubeMX often stores: enabled:preempt:sub:...; keep raw and best-effort parse.
            enabled = None
            preempt = None
            sub = None
            if parts:
                enabled = parts[0].lower() in {'true', '1', 'enabled'}
            ints = []
            for p in parts[1:4]:
                try:
                    ints.append(int(p, 0))
                except ValueError:
                    pass
            if ints:
                preempt = ints[0]
            if len(ints) > 1:
                sub = ints[1]
            nvic.append({'irq': k[len('NVIC.'):], 'enabled': enabled, 'preempt_priority': preempt, 'sub_priority': sub, 'raw': v})

    clocks = {k: v for k, v in raw.items() if k.startswith('RCC.') or k.startswith('Mcu.IP') and 'RCC' in v}
    freertos = {k: v for k, v in raw.items() if k.startswith('FREERTOS.') or k.startswith('FreeRTOS.')}
    fatfs = {k: v for k, v in raw.items() if k.startswith('FATFS.')}

    peripherals = defaultdict(dict)
    periph_prefixes = ('USART', 'UART', 'SPI', 'I2C', 'I3C', 'ADC', 'DAC', 'TIM', 'LPTIM', 'CAN', 'FDCAN', 'SDIO', 'SDMMC', 'RTC', 'RNG', 'USB', 'ETH')
    for k, v in raw.items():
        top = k.split('.', 1)[0]
        if top.startswith(periph_prefixes):
            peripherals[top][k.split('.', 1)[1] if '.' in k else 'value'] = v

    middleware = [ip for ip in ips if ip.upper() in {'FREERTOS', 'FATFS', 'LWIP', 'USB_DEVICE', 'USB_HOST', 'TOUCHGFX', 'MBEDTLS'}]

    return {
        'ioc_file': str(path),
        'mcu': mcu,
        'project': project,
        'ips': ips,
        'middleware': middleware,
        'pins': pin_rows,
        'virtual_pins': [{'name': k, 'raw': v} for k, v in sorted(virtual_pins.items())],
        'dma': dma,
        'nvic': nvic,
        'clocks': clocks,
        'freertos': freertos,
        'fatfs': fatfs,
        'peripherals': dict(sorted(peripherals.items())),
        'raw_count': len(raw),
    }


def discover_ioc(root: Path) -> Path | None:
    files = sorted(root.glob('*.ioc'))
    if len(files) == 1:
        return files[0]
    if not files:
        files = sorted(root.rglob('*.ioc'))
        if len(files) == 1:
            return files[0]
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description='Parse STM32CubeMX .ioc into machine-readable JSON')
    ap.add_argument('project', nargs='?', default='.', help='project root or .ioc file')
    ap.add_argument('--ioc', help='explicit .ioc path')
    ap.add_argument('--output', '-o', help='output JSON path')
    ap.add_argument('--json', action='store_true', help='print JSON to stdout')
    args = ap.parse_args()

    p = Path(args.ioc or args.project).resolve()
    if p.suffix.lower() == '.ioc':
        ioc = p
        root = p.parent
    else:
        root = find_project_root(p)
        ioc = Path(args.ioc).resolve() if args.ioc else discover_ioc(root)
        if ioc is None:
            raise SystemExit('No unique .ioc file found. Use --ioc explicitly.')

    data = parse_ioc_file(ioc)
    if args.output:
        write_json(Path(args.output), data)
    elif args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"IOC: {ioc}")
        print(f"MCU: {data['mcu'].get('name') or '?'} / {data['mcu'].get('family') or '?'}")
        print(f"Pins: {len(data['pins'])}, IPs: {len(data['ips'])}, NVIC: {len(data['nvic'])}, DMA entries: {len(data['dma'])}")


if __name__ == '__main__':
    main()
