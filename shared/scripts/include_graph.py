#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from _common import LAYER_ORDER, classify_layer, find_project_root, iter_source_files, norm_rel, read_text, write_json

INC_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.M)


def build_graph(root: Path, include_generated: bool = False) -> dict:
    files = list(iter_source_files(root, include_generated=include_generated))
    by_name: dict[str, list[str]] = defaultdict(list)
    all_rel = []
    for p in files:
        rel = norm_rel(p, root)
        all_rel.append(rel)
        by_name[p.name].append(rel)

    edges = []
    unresolved = []
    violations = []
    for p in files:
        src = norm_rel(p, root)
        src_layer = classify_layer(src)
        text = read_text(p)
        for inc in INC_RE.findall(text):
            target = None
            candidates = by_name.get(Path(inc).name, [])
            if len(candidates) == 1:
                target = candidates[0]
            elif len(candidates) > 1:
                # Prefer suffix path match, then same directory.
                suffix_matches = [c for c in candidates if c.endswith(inc.replace('\\', '/'))]
                if len(suffix_matches) == 1:
                    target = suffix_matches[0]
                else:
                    same_dir = [c for c in candidates if Path(c).parent == Path(src).parent]
                    if len(same_dir) == 1:
                        target = same_dir[0]
            if target:
                dst_layer = classify_layer(target)
                edges.append({'from': src, 'to': target, 'include': inc, 'from_layer': src_layer, 'to_layer': dst_layer})
                sr = LAYER_ORDER.get(src_layer, 50)
                dr = LAYER_ORDER.get(dst_layer, 50)
                # Upper layers may depend on lower. Lower depending on upper is forbidden.
                if src_layer not in {'common', 'config', 'tests', 'unknown'} and dst_layer not in {'common', 'config', 'tests', 'unknown'}:
                    if sr < dr:
                        violations.append({
                            'severity': 'high', 'type': 'upward_dependency',
                            'from': src, 'to': target,
                            'message': f'{src_layer} (L{sr}) depends on higher {dst_layer} (L{dr})',
                        })
            else:
                unresolved.append({'from': src, 'include': inc})

    layer_edges = defaultdict(int)
    for e in edges:
        layer_edges[(e['from_layer'], e['to_layer'])] += 1

    return {
        'project': str(root),
        'files': sorted(all_rel),
        'edges': edges,
        'unresolved': unresolved,
        'violations': violations,
        'layer_edges': [
            {'from_layer': a, 'to_layer': b, 'count': n}
            for (a, b), n in sorted(layer_edges.items())
        ],
    }


def write_dot(data: dict, path: Path) -> None:
    lines = ['digraph includes {', '  rankdir=LR;', '  node [shape=box,fontname="Arial"];']
    for f in data['files']:
        layer = classify_layer(f)
        safe = f.replace('"', '\\"')
        lines.append(f'  "{safe}" [label="{safe}\\n[{layer}]"];')
    for e in data['edges']:
        a = e['from'].replace('"', '\\"')
        b = e['to'].replace('"', '\\"')
        lines.append(f'  "{a}" -> "{b}";')
    lines.append('}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_mermaid(data: dict, path: Path) -> None:
    ids = {f: f'n{i}' for i, f in enumerate(data['files'])}
    lines = ['flowchart LR']
    for f, nid in ids.items():
        label = f.replace('"', "'")
        lines.append(f'  {nid}["{label}"]')
    for e in data['edges']:
        if e['from'] in ids and e['to'] in ids:
            lines.append(f"  {ids[e['from']]} --> {ids[e['to']]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    ap = argparse.ArgumentParser(description='Generate C/C++ include dependency graph and layer violations')
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--include-generated', action='store_true')
    ap.add_argument('--output', '-o', help='JSON output')
    ap.add_argument('--dot', help='DOT output')
    ap.add_argument('--mermaid', help='Mermaid output')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    root = find_project_root(args.project)
    data = build_graph(root, args.include_generated)
    if args.output:
        write_json(Path(args.output), data)
    if args.dot:
        write_dot(data, Path(args.dot))
    if args.mermaid:
        write_mermaid(data, Path(args.mermaid))
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif not (args.output or args.dot or args.mermaid):
        print(f"Files={len(data['files'])} Edges={len(data['edges'])} Violations={len(data['violations'])} Unresolved={len(data['unresolved'])}")
        for v in data['violations'][:20]:
            print(f"[HIGH] {v['from']} -> {v['to']}: {v['message']}")


if __name__ == '__main__':
    main()
