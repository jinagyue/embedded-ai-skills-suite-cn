#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _common import find_project_root

SUPPORTED = {'plan', 'build', 'build-flash', 'build-debug', 'observe', 'diagnose'}


def invoke(root: Path, workspace: Path, action: str, extra: list[str] | None = None) -> dict:
    script = root / 'workflow' / 'scripts' / 'workflow_run.py'
    if not script.exists():
        return {
            'status': 'error',
            'error': {'code': 'missing_workflow', 'message': f'Not found: {script}'},
        }
    cmd = [sys.executable, str(script), action, '--workspace', str(workspace), '--json']
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    payload = (proc.stdout or proc.stderr).strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = {
            'status': 'error',
            'error': {'code': 'invalid_json', 'message': payload[-2000:] or 'no output'},
            'command': cmd,
            'returncode': proc.returncode,
        }
    data.setdefault('adapter', {})
    data['adapter'].update({'root': str(root), 'workspace': str(workspace), 'action': action, 'returncode': proc.returncode})
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description='Bridge this suite to zhinkgit/embeddedskills workflow')
    ap.add_argument('--embeddedskills-root', required=True, help='local clone path of zhinkgit/embeddedskills')
    ap.add_argument('--workspace', default='.')
    ap.add_argument('--action', choices=sorted(SUPPORTED), default='diagnose')
    ap.add_argument('--build-backend', choices=['auto', 'keil', 'gcc', 'eide'])
    ap.add_argument('--flash-backend', choices=['auto', 'jlink', 'openocd', 'probe-rs'])
    ap.add_argument('--debug-backend', choices=['auto', 'jlink', 'openocd', 'probe-rs'])
    ap.add_argument('--observe-backend', choices=['auto', 'jlink', 'openocd', 'probe-rs'])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    extra = []
    for key in ('build_backend', 'flash_backend', 'debug_backend', 'observe_backend'):
        value = getattr(args, key)
        if value:
            extra.extend(['--' + key.replace('_', '-'), value])
    data = invoke(Path(args.embeddedskills_root).resolve(), find_project_root(args.workspace), args.action, extra)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data.get('summary') or data.get('error') or data)
    if data.get('status') == 'error':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
