#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description='Capture serial logs for finite duration')
    ap.add_argument('--port', required=True)
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--duration', type=float, default=5.0)
    ap.add_argument('--output', required=True)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    try:
        import serial  # type: ignore
    except Exception as exc:
        raise SystemExit(f'pyserial is required: {exc}')

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    started = time.time()
    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        while time.time() - started < args.duration:
            raw = ser.readline()
            if not raw:
                continue
            text = raw.decode('utf-8', errors='replace').rstrip('\r\n')
            stamp = time.time() - started
            lines.append(f'[{stamp:8.3f}] {text}')
    out.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
    result = {'status': 'ok', 'port': args.port, 'baud': args.baud, 'duration': args.duration, 'lines': len(lines), 'output': str(out)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Captured {len(lines)} lines -> {out}")


if __name__ == '__main__':
    main()
