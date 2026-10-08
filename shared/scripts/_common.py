from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Iterable, Iterator

SOURCE_SUFFIXES = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx'}
GENERATED_PREFIXES = (
    'Drivers/', 'Middlewares/', 'USB_DEVICE/', 'FATFS/', 'LWIP/', 'TouchGFX/',
)

LAYER_ORDER = {
    'vendor': 1,
    'bsp_driver': 2,
    'platform': 3,
    'device': 3,
    'protocol': 3,
    'service': 4,
    'app': 5,
    'rtos': 5,
    'common': 0,
    'config': 0,
    'tests': 99,
    'unknown': 50,
}


def norm_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def classify_layer(rel: str) -> str:
    p = rel.replace('\\', '/').lstrip('./')
    lower = p.lower()
    if lower.startswith('drivers/') or lower.startswith('core/'):
        return 'vendor'
    if lower.startswith('bsp/driver/'):
        return 'bsp_driver'
    if lower.startswith('bsp/service/') or lower.startswith('bsp/board/') or lower.startswith('bsp/port/'):
        return 'platform'
    if lower.startswith('device/'):
        return 'device'
    if lower.startswith('protocol/'):
        return 'protocol'
    if lower.startswith('service/'):
        return 'service'
    if lower.startswith('app/'):
        return 'app'
    if lower.startswith('rtos/'):
        return 'rtos'
    if lower.startswith('common/'):
        return 'common'
    if lower.startswith('config/'):
        return 'config'
    if lower.startswith('tests/') or lower.startswith('test/'):
        return 'tests'
    return 'unknown'


def iter_source_files(root: Path, *, include_generated: bool = False) -> Iterator[Path]:
    root = root.resolve()
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        rel = norm_rel(path, root)
        if not include_generated and any(rel.startswith(prefix) for prefix in GENERATED_PREFIXES):
            continue
        if '/build/' in f'/{rel.lower()}/' or '/mdk-arm/' in f'/{rel.lower()}/' or '/.git/' in f'/{rel.lower()}/':
            continue
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return ''


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load_json(path: Path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def find_project_root(start: str | Path) -> Path:
    p = Path(start).resolve()
    if p.is_file():
        p = p.parent
    markers = ('*.ioc', '*.uvprojx', 'CMakeLists.txt')
    cur = p
    while True:
        if any(cur.glob(m) for m in markers) or (cur / 'Core').exists() or (cur / 'App').exists():
            return cur
        if cur.parent == cur:
            return p
        cur = cur.parent


def strip_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'//.*', '', text)
    return text


def find_functions(text: str) -> list[dict]:
    """Heuristic C function extractor; enough for static project mapping, not a parser."""
    clean = strip_comments(text)
    pattern = re.compile(
        r'(?P<sig>(?:static\s+)?(?:inline\s+)?(?:[A-Za-z_]\w*[\s\*]+)+(?P<name>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*)\{',
        re.M,
    )
    out = []
    for m in pattern.finditer(clean):
        start = m.end() - 1
        depth = 0
        end = start
        for i in range(start, len(clean)):
            ch = clean[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        out.append({'name': m.group('name'), 'start': m.start(), 'end': end, 'body': clean[start:end]})
    return out


def line_number(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def severity_rank(s: str) -> int:
    return {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0}.get(s.lower(), 0)


def shell_quote_arg(arg: str) -> str:
    if os.name == 'nt':
        if re.search(r'[\s"]', arg):
            return '"' + arg.replace('"', '\\"') + '"'
        return arg
    import shlex
    return shlex.quote(arg)
