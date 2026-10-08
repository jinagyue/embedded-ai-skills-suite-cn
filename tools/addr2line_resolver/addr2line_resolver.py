#!/usr/bin/env python3
"""arm-none-eabi-addr2line 中文封装。

支持：
- 直接给地址；
- 从 HardFault/串口/GDB 日志提取 0x... 地址；
- 自动寻找 arm-none-eabi-addr2line；
- 输出 JSON，供 AI 调试闭环消费。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

ADDR_RE = re.compile(r"\b0x[0-9A-Fa-f]{6,16}\b")


def normalize_addr(s: str) -> str:
    return f"0x{int(s, 0):X}"


def extract_addresses(text: str) -> list[str]:
    out = []
    seen = set()
    for m in ADDR_RE.finditer(text):
        a = normalize_addr(m.group(0))
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def find_tool(explicit: str | None = None, prefix: str = 'arm-none-eabi-') -> str | None:
    if explicit:
        p = Path(explicit)
        if p.exists():
            return str(p)
        q = shutil.which(explicit)
        return q
    return shutil.which(prefix + 'addr2line') or shutil.which('addr2line')


def resolve(tool: str, elf: Path, addresses: list[str]) -> list[dict[str, Any]]:
    if not addresses:
        return []
    cmd = [tool, '-e', str(elf), '-a', '-f', '-C', '-i', *addresses]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or 'addr2line failed').strip())

    # GNU addr2line -a -f -i: 每个输入地址通常以地址行开头，后跟函数/文件，可有 inline 对。
    groups: list[dict[str, Any]] = []
    cur = None
    lines = p.stdout.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.fullmatch(r'0x[0-9A-Fa-f]+', line):
            if cur:
                groups.append(cur)
            cur = {'address': normalize_addr(line), 'frames': []}
            i += 1
            continue
        if cur is None:
            i += 1
            continue
        fn = line
        loc = lines[i + 1].strip() if i + 1 < len(lines) else '??:0'
        cur['frames'].append({'function': fn, 'location': loc})
        i += 2
    if cur:
        groups.append(cur)

    # 某些实现可能不回显 -a；做回退映射。
    if not groups:
        pairs = []
        for j in range(0, len(lines), 2):
            pairs.append({'address': addresses[min(j // 2, len(addresses)-1)], 'frames': [{'function': lines[j].strip(), 'location': lines[j+1].strip() if j+1 < len(lines) else '??:0'}]})
        groups = pairs
    return groups


def main() -> None:
    ap = argparse.ArgumentParser(description='arm-none-eabi-addr2line 自动源码定位')
    ap.add_argument('--elf', required=True)
    ap.add_argument('addresses', nargs='*')
    ap.add_argument('--log', help='从日志中提取 0x 地址')
    ap.add_argument('--tool', help='addr2line 可执行文件路径/命令名')
    ap.add_argument('--tool-prefix', default='arm-none-eabi-')
    ap.add_argument('--json-out')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--allow-missing-tool', action='store_true', help='工具链不存在时返回 unresolved 而不是报错')
    args = ap.parse_args()

    elf = Path(args.elf).resolve()
    if not elf.exists():
        ap.error(f'ELF 不存在：{elf}')

    addresses = [normalize_addr(a) for a in args.addresses]
    if args.log:
        lp = Path(args.log)
        if not lp.exists():
            ap.error(f'日志不存在：{lp}')
        for a in extract_addresses(lp.read_text(encoding='utf-8', errors='replace')):
            if a not in addresses:
                addresses.append(a)
    if not addresses:
        ap.error('请提供地址，或通过 --log 提供含地址的日志')

    tool = find_tool(args.tool, args.tool_prefix)
    result: dict[str, Any] = {'elf': str(elf), 'tool': tool, 'addresses': addresses, 'resolved': []}
    if not tool:
        result['status'] = 'tool_missing'
        result['message'] = '未找到 arm-none-eabi-addr2line。请安装 GNU Arm Embedded Toolchain 或使用 --tool 指定路径。'
        if not args.allow_missing_tool:
            print(result['message'])
            raise SystemExit(2)
    else:
        try:
            result['resolved'] = resolve(tool, elf, addresses)
            result['status'] = 'ok'
        except Exception as exc:
            result['status'] = 'error'
            result['message'] = str(exc)
            if not args.allow_missing_tool:
                raise SystemExit(str(exc))

    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ELF：{elf}")
        print(f"Tool：{tool or '未找到'}")
        for row in result['resolved']:
            print(row['address'])
            for fr in row['frames']:
                print(f"  {fr['function']} -> {fr['location']}")


if __name__ == '__main__':
    main()
