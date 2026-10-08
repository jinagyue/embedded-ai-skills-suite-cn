#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = 'https://github.com/zhinkgit/embeddedskills.git'


def main() -> None:
    ap = argparse.ArgumentParser(description='Install/update optional zhinkgit/embeddedskills debug backend')
    ap.add_argument('--dest', default=str(Path.home() / '.embedded-ai-tools' / 'embeddedskills'))
    ap.add_argument('--update', action='store_true')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    dest = Path(args.dest).expanduser().resolve()
    if (dest / '.git').exists():
        if args.update:
            p = subprocess.run(['git', '-C', str(dest), 'pull', '--ff-only'], capture_output=True, text=True)
        else:
            p = None
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.run(['git', 'clone', '--depth', '1', REPO, str(dest)], capture_output=True, text=True)
        if p.returncode != 0:
            raise SystemExit(p.stderr or p.stdout)
    ok = (dest / 'workflow' / 'scripts' / 'workflow_run.py').exists()
    result = {'status': 'ok' if ok else 'error', 'path': str(dest), 'repo': REPO, 'workflow_found': ok}
    if p is not None:
        result['git_stdout'] = p.stdout[-2000:]
        result['git_stderr'] = p.stderr[-2000:]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"embeddedskills backend: {dest}")
        print('workflow OK' if ok else 'workflow not found')
    if not ok:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
