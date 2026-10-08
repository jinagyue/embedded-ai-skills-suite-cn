#!/usr/bin/env python3
"""Keil/Arm Linker .map 固件分析工具。

目标：把 MDK-ARM / armlink 生成的 .map 中最有价值的信息转成结构化证据：
- Program Size（Code/RO/RW/ZI）
- Execution Region / Load Region
- Image component sizes（对象/库成员的 Code/RO/RW/ZI 贡献）
- 符号表中的较大函数/对象（尽力解析，不保证所有 armlink 版本格式完全一致）

不依赖第三方包。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PROGRAM_SIZE_RE = re.compile(
    r"Program\s+Size:\s*Code=(?P<code>\d+)\s+RO-data=(?P<ro>\d+)\s+RW-data=(?P<rw>\d+)\s+ZI-data=(?P<zi>\d+)",
    re.I,
)
REGION_RE = re.compile(
    r"(?P<kind>Execution|Load)\s+Region\s+(?P<name>\S+)\s*\("
    r"(?P<body>[^\)]*)\)",
    re.I,
)
HEX_FIELD_RE = re.compile(r"(?P<key>[A-Za-z ]+):\s*0x(?P<value>[0-9A-Fa-f]+)")
COMPONENT_HEADER_RE = re.compile(r"Image\s+component\s+sizes", re.I)
# 常见 armlink component 行：
#  123   4   0   8   16   0   foo.o
COMPONENT_ROW_RE = re.compile(
    r"^\s*(?P<code>\d+)\s+(?P<incdata>\d+)\s+(?P<ro>\d+)\s+(?P<rw>\d+)\s+(?P<zi>\d+)\s+(?P<debug>\d+)\s+(?P<name>.+?)\s*$"
)
# 常见符号表：name  0xADDR  Thumb Code  SIZE  object
SYMBOL_ROW_RE = re.compile(
    r"^\s*(?P<name>\S+)\s+0x(?P<addr>[0-9A-Fa-f]+)\s+"
    r"(?P<stype>Thumb\s+Code|ARM\s+Code|Code|Data|Number|Section)\s+"
    r"(?P<size>\d+)\s+(?P<object>.+?)\s*$"
)


def human_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.2f} MiB"
    if n >= 1024:
        return f"{n / 1024:.1f} KiB"
    return f"{n} B"


def parse_region(line: str) -> dict[str, Any] | None:
    m = REGION_RE.search(line)
    if not m:
        return None
    body = m.group('body')
    fields: dict[str, int] = {}
    for fm in HEX_FIELD_RE.finditer(body):
        key = fm.group('key').strip().lower().replace(' ', '_')
        fields[key] = int(fm.group('value'), 16)
    return {
        'kind': m.group('kind').lower(),
        'name': m.group('name'),
        'fields': fields,
        'raw': line.strip(),
    }


def parse_map(path: Path, top: int = 30) -> dict[str, Any]:
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()

    summary = None
    m = PROGRAM_SIZE_RE.search(text)
    if m:
        code = int(m.group('code'))
        ro = int(m.group('ro'))
        rw = int(m.group('rw'))
        zi = int(m.group('zi'))
        summary = {
            'code_bytes': code,
            'ro_data_bytes': ro,
            'rw_data_bytes': rw,
            'zi_data_bytes': zi,
            # Keil 常见近似：Flash = Code + RO + RW；RAM = RW + ZI
            'estimated_flash_bytes': code + ro + rw,
            'estimated_ram_bytes': rw + zi,
        }

    regions = []
    for line in lines:
        r = parse_region(line)
        if r:
            regions.append(r)

    components = []
    in_components = False
    blank_streak = 0
    for line in lines:
        if COMPONENT_HEADER_RE.search(line):
            in_components = True
            blank_streak = 0
            continue
        if not in_components:
            continue
        if not line.strip():
            blank_streak += 1
            if blank_streak >= 3 and components:
                in_components = False
            continue
        blank_streak = 0
        cm = COMPONENT_ROW_RE.match(line)
        if cm:
            row = {k: int(cm.group(k)) for k in ('code', 'incdata', 'ro', 'rw', 'zi', 'debug')}
            row['name'] = cm.group('name').strip()
            row['flash_bytes'] = row['code'] + row['ro'] + row['rw']
            row['ram_bytes'] = row['rw'] + row['zi']
            components.append(row)

    symbols = []
    for line in lines:
        sm = SYMBOL_ROW_RE.match(line)
        if not sm:
            continue
        stype = re.sub(r'\s+', ' ', sm.group('stype').strip())
        symbols.append({
            'name': sm.group('name'),
            'address': int(sm.group('addr'), 16),
            'type': stype,
            'size': int(sm.group('size')),
            'object': sm.group('object').strip(),
        })

    funcs = [s for s in symbols if 'Code' in s['type']]
    data = [s for s in symbols if s['type'] == 'Data']
    funcs.sort(key=lambda x: x['size'], reverse=True)
    data.sort(key=lambda x: x['size'], reverse=True)
    comp_flash = sorted(components, key=lambda x: x['flash_bytes'], reverse=True)
    comp_ram = sorted(components, key=lambda x: x['ram_bytes'], reverse=True)

    return {
        'file': str(path),
        'program_size': summary,
        'regions': regions,
        'component_count': len(components),
        'components': components,
        'symbol_count': len(symbols),
        'largest_functions': funcs[:top],
        'largest_data_symbols': data[:top],
        'largest_flash_components': comp_flash[:top],
        'largest_ram_components': comp_ram[:top],
        'parser_notes': [
            'Program Size 与 Image component sizes 基于 Keil/Arm Linker 常见格式解析。',
            '符号表格式在不同 armlink 版本间可能变化；无法识别的行会被跳过。',
        ],
    }


def render_markdown(r: dict[str, Any]) -> str:
    lines = ['# Keil MAP 固件分析报告', '', f"- 文件：`{r['file']}`"]
    ps = r.get('program_size')
    if ps:
        lines += [
            f"- Code：**{human_bytes(ps['code_bytes'])}**",
            f"- RO-data：**{human_bytes(ps['ro_data_bytes'])}**",
            f"- RW-data：**{human_bytes(ps['rw_data_bytes'])}**",
            f"- ZI-data：**{human_bytes(ps['zi_data_bytes'])}**",
            f"- 估算 Flash：**{human_bytes(ps['estimated_flash_bytes'])}**",
            f"- 估算 RAM：**{human_bytes(ps['estimated_ram_bytes'])}**",
        ]
    else:
        lines += ['- 未识别到 `Program Size` 汇总行。']

    lines += ['', '## Execution / Load Region', '']
    if r['regions']:
        for x in r['regions']:
            fields = ', '.join(f"{k}=0x{v:X}" for k, v in x['fields'].items())
            lines.append(f"- `{x['kind']}` `{x['name']}`：{fields}")
    else:
        lines.append('未识别到 region。')

    lines += ['', '## Flash 占用最大的组件', '']
    if r['largest_flash_components']:
        for x in r['largest_flash_components']:
            lines.append(f"- `{x['name']}`：{x['flash_bytes']} B（Code {x['code']} / RO {x['ro']} / RW {x['rw']}）")
    else:
        lines.append('未识别到 Image component sizes。')

    lines += ['', '## RAM 占用最大的组件', '']
    if r['largest_ram_components']:
        for x in r['largest_ram_components']:
            lines.append(f"- `{x['name']}`：{x['ram_bytes']} B（RW {x['rw']} / ZI {x['zi']}）")
    else:
        lines.append('未识别到 Image component sizes。')

    lines += ['', '## 最大函数', '']
    if r['largest_functions']:
        for x in r['largest_functions']:
            lines.append(f"- `{x['name']}`：{x['size']} B @ `0x{x['address']:08X}` ({x['object']})")
    else:
        lines.append('未从符号表中识别到函数大小。')

    lines += ['', '## 最大数据符号', '']
    if r['largest_data_symbols']:
        for x in r['largest_data_symbols']:
            lines.append(f"- `{x['name']}`：{x['size']} B @ `0x{x['address']:08X}` ({x['object']})")
    else:
        lines.append('未从符号表中识别到数据符号大小。')

    lines += ['', '## 解析说明', ''] + [f"- {x}" for x in r['parser_notes']]
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser(description='Keil/Arm Linker .map 中文分析工具')
    ap.add_argument('map_file')
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--json-out')
    ap.add_argument('--report')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    path = Path(args.map_file).resolve()
    if not path.exists():
        ap.error(f'MAP 文件不存在：{path}')
    result = parse_map(path, max(1, args.top))

    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.report:
        p = Path(args.report)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(render_markdown(result), encoding='utf-8')

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('Keil MAP：', path)
        ps = result.get('program_size')
        if ps:
            print(f"Flash≈{human_bytes(ps['estimated_flash_bytes'])}  RAM≈{human_bytes(ps['estimated_ram_bytes'])}")
        else:
            print('未识别 Program Size 汇总。')
        print(f"Regions={len(result['regions'])} Components={result['component_count']} Symbols={result['symbol_count']}")
        if args.json_out:
            print('JSON 报告：', args.json_out)
        if args.report:
            print('Markdown 报告：', args.report)


if __name__ == '__main__':
    main()
