#!/usr/bin/env python3
"""ARM Cortex-M HardFault 自动解码器。

可从日志提取：CFSR/HFSR/DFSR/SHCSR/MMFAR/BFAR、R0-R3/R12/LR/PC/xPSR/MSP/PSP。
随后：
1. 解码 Cortex-M fault status bits；
2. 解码 EXC_RETURN 与 xPSR；
3. 若提供 ELF，则调用 addr2line 定位 PC/LR 到源码。

不替代芯片参考手册；不同 Cortex-M 内核支持的 fault 位可能不同。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

REG_NAMES = [
    'CFSR','HFSR','DFSR','AFSR','SHCSR','MMFAR','BFAR',
    'R0','R1','R2','R3','R12','LR','PC','XPSR','MSP','PSP','SP','EXC_RETURN'
]

CFSR_BITS = {
    0: ('IACCVIOL', 'MemManage：取指访问违规'),
    1: ('DACCVIOL', 'MemManage：数据访问违规'),
    3: ('MUNSTKERR', 'MemManage：异常返回出栈时错误'),
    4: ('MSTKERR', 'MemManage：异常进入压栈时错误'),
    5: ('MLSPERR', 'MemManage：惰性浮点状态保存错误'),
    7: ('MMARVALID', 'MMFAR 有效'),
    8: ('IBUSERR', 'BusFault：取指总线错误'),
    9: ('PRECISERR', 'BusFault：精确数据总线错误，堆栈 PC 通常可信'),
    10: ('IMPRECISERR', 'BusFault：非精确数据总线错误，堆栈 PC 可能不是真正故障指令'),
    11: ('UNSTKERR', 'BusFault：异常返回出栈错误'),
    12: ('STKERR', 'BusFault：异常进入压栈错误'),
    13: ('LSPERR', 'BusFault：惰性浮点状态保存错误'),
    15: ('BFARVALID', 'BFAR 有效'),
    16: ('UNDEFINSTR', 'UsageFault：执行未定义指令'),
    17: ('INVSTATE', 'UsageFault：无效 EPSR/Thumb 状态'),
    18: ('INVPC', 'UsageFault：异常返回时无效 PC/EXC_RETURN'),
    19: ('NOCP', 'UsageFault：协处理器不可用'),
    20: ('STKOF', 'UsageFault：栈溢出（仅部分 Cortex-M，如 M33）'),
    24: ('UNALIGNED', 'UsageFault：非对齐访问'),
    25: ('DIVBYZERO', 'UsageFault：除零'),
}
HFSR_BITS = {
    1: ('VECTTBL', 'HardFault：取异常向量时总线错误'),
    30: ('FORCED', 'HardFault：可配置 Fault 升级为 HardFault'),
    31: ('DEBUGEVT', 'HardFault：调试事件触发'),
}
DFSR_BITS = {
    0: ('HALTED', '调试 Halt'),
    1: ('BKPT', 'BKPT 指令'),
    2: ('DWTTRAP', 'DWT trap'),
    3: ('VCATCH', 'Vector catch'),
    4: ('EXTERNAL', '外部调试请求'),
}


def parse_int(v: str) -> int:
    return int(v.strip(), 0)


def parse_registers(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in REG_NAMES:
        # 支持 CFSR=0x... / CFSR : 0x... / "CFSR": "0x..."
        pat = re.compile(rf'(?i)(?<![A-Za-z0-9_])(?:["\']?{re.escape(name)}["\']?)(?![A-Za-z0-9_])\s*[:=]\s*["\']?(0x[0-9a-f]+|\d+)')
        matches = list(pat.finditer(text))
        if matches:
            try:
                out[name] = parse_int(matches[-1].group(1))
            except ValueError:
                pass
    return out


def decode_bits(value: int, table: dict[int, tuple[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for bit, (name, desc) in sorted(table.items()):
        if value & (1 << bit):
            rows.append({'bit': bit, 'name': name, 'description': desc})
    return rows


def decode_exc_return(lr: int | None) -> dict[str, Any] | None:
    if lr is None or (lr & 0xFF000000) != 0xFF000000:
        return None
    return {
        'raw': lr,
        'looks_like_exc_return': True,
        'stack_used': 'PSP' if (lr & (1 << 2)) else 'MSP',
        'return_to': 'Thread mode' if (lr & (1 << 3)) else 'Handler mode',
        'fp_context': '未压栈扩展浮点上下文' if (lr & (1 << 4)) else '压栈了扩展浮点上下文',
    }


def decode_xpsr(xpsr: int | None) -> dict[str, Any] | None:
    if xpsr is None:
        return None
    return {
        'raw': xpsr,
        'exception_number': xpsr & 0x1FF,
        'thumb_state': bool(xpsr & (1 << 24)),
        'q_flag': bool(xpsr & (1 << 27)),
        'n_flag': bool(xpsr & (1 << 31)),
        'z_flag': bool(xpsr & (1 << 30)),
        'c_flag': bool(xpsr & (1 << 29)),
        'v_flag': bool(xpsr & (1 << 28)),
    }


def load_addr2line_module() -> Any:
    path = Path(__file__).resolve().parents[1] / 'addr2line_resolver' / 'addr2line_resolver.py'
    spec = importlib.util.spec_from_file_location('addr2line_resolver_local', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('无法加载 addr2line_resolver')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_pc_lr(elf: Path | None, regs: dict[str, int], tool: str | None, prefix: str) -> dict[str, Any] | None:
    if elf is None:
        return None
    addrs = []
    if 'PC' in regs:
        addrs.append(f"0x{regs['PC']:X}")
    if 'LR' in regs and (regs['LR'] & 0xFF000000) != 0xFF000000:
        addrs.append(f"0x{regs['LR']:X}")
    if not addrs:
        return None
    mod = load_addr2line_module()
    exe = mod.find_tool(tool, prefix)
    if not exe:
        return {'status': 'tool_missing', 'message': '未找到 arm-none-eabi-addr2line', 'addresses': addrs}
    try:
        rows = mod.resolve(exe, elf, addrs)
        return {'status': 'ok', 'tool': exe, 'resolved': rows}
    except Exception as exc:
        return {'status': 'error', 'tool': exe, 'message': str(exc), 'addresses': addrs}


def analyze(text: str, elf: Path | None = None, tool: str | None = None, prefix: str = 'arm-none-eabi-') -> dict[str, Any]:
    regs = parse_registers(text)
    cfsr = regs.get('CFSR', 0)
    hfsr = regs.get('HFSR', 0)
    dfsr = regs.get('DFSR', 0)
    result = {
        'registers': {k: {'value': v, 'hex': f'0x{v:08X}'} for k, v in regs.items()},
        'cfsr_flags': decode_bits(cfsr, CFSR_BITS),
        'hfsr_flags': decode_bits(hfsr, HFSR_BITS),
        'dfsr_flags': decode_bits(dfsr, DFSR_BITS),
        'exc_return': decode_exc_return(regs.get('EXC_RETURN', regs.get('LR'))),
        'xpsr': decode_xpsr(regs.get('XPSR')),
        'source_resolution': resolve_pc_lr(elf, regs, tool, prefix),
        'diagnosis': [],
    }
    d = result['diagnosis']
    names = {x['name'] for x in result['cfsr_flags']}
    if 'PRECISERR' in names and 'BFARVALID' in names and 'BFAR' in regs:
        d.append(f"精确 BusFault：优先检查 BFAR=0x{regs['BFAR']:08X} 与堆栈 PC。")
    if 'IMPRECISERR' in names:
        d.append('检测到非精确 BusFault：PC 可能不是根因地址；建议暂时关闭写缓冲/使用 DSB 或硬件 watchpoint 缩小范围。')
    if 'MMARVALID' in names and 'MMFAR' in regs:
        d.append(f"MemManage 地址有效：MMFAR=0x{regs['MMFAR']:08X}。")
    if 'UNDEFINSTR' in names or 'INVSTATE' in names or 'INVPC' in names:
        d.append('UsageFault 与执行流/返回地址异常相关：检查函数指针、栈破坏、Thumb bit、异常返回。')
    if 'DIVBYZERO' in names:
        d.append('发生除零：检查除数边界与 DIV_0_TRP 配置。')
    if 'UNALIGNED' in names:
        d.append('发生非对齐访问：检查 packed 结构、强制类型转换、DMA/协议缓冲区对齐。')
    if any(x in names for x in ('MSTKERR','STKERR','MUNSTKERR','UNSTKERR','STKOF')):
        d.append('Fault 与异常压栈/出栈或栈空间相关：优先检查 MSP/PSP、任务栈、ISR 嵌套和栈越界。')
    if not d and (cfsr or hfsr):
        d.append('已检测到 Fault 状态位，但没有命中特定快捷诊断；结合芯片内核版本与参考手册继续分析。')
    if not regs:
        d.append('日志中未识别到 Fault 寄存器。建议输出 CFSR/HFSR/MMFAR/BFAR 与堆栈 R0-R3/R12/LR/PC/xPSR。')
    return result


def render_markdown(r: dict[str, Any]) -> str:
    lines = ['# HardFault 自动解码报告', '', '## 寄存器', '']
    if r['registers']:
        for k, v in r['registers'].items():
            lines.append(f"- `{k}` = `{v['hex']}`")
    else:
        lines.append('未识别到寄存器。')

    for title, key in [('CFSR 解码','cfsr_flags'), ('HFSR 解码','hfsr_flags'), ('DFSR 解码','dfsr_flags')]:
        lines += ['', f'## {title}', '']
        if r[key]:
            for x in r[key]:
                lines.append(f"- bit{x['bit']} `{x['name']}`：{x['description']}")
        else:
            lines.append('无已置位的已知标志。')

    if r.get('exc_return'):
        x = r['exc_return']
        lines += ['', '## EXC_RETURN', '', f"- 使用栈：**{x['stack_used']}**", f"- 返回到：**{x['return_to']}**", f"- 浮点上下文：{x['fp_context']}"]
    if r.get('xpsr'):
        x = r['xpsr']
        lines += ['', '## xPSR', '', f"- Exception number：{x['exception_number']}", f"- Thumb state：{x['thumb_state']}"]

    lines += ['', '## 源码定位', '']
    sr = r.get('source_resolution')
    if sr and sr.get('status') == 'ok':
        for row in sr.get('resolved', []):
            lines.append(f"- `{row['address']}`")
            for fr in row.get('frames', []):
                lines.append(f"  - `{fr['function']}` → `{fr['location']}`")
    elif sr:
        lines.append(sr.get('message', sr.get('status', '未解析')))
    else:
        lines.append('未提供 ELF，未执行 addr2line。')

    lines += ['', '## 诊断建议', '']
    for x in r['diagnosis']:
        lines.append(f'- {x}')
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser(description='Cortex-M HardFault 中文自动解码器')
    ap.add_argument('--log', help='HardFault 日志文件；未提供时从 stdin 读取')
    ap.add_argument('--elf', help='可选 ELF，用于 addr2line')
    ap.add_argument('--tool', help='arm-none-eabi-addr2line 路径/命令')
    ap.add_argument('--tool-prefix', default='arm-none-eabi-')
    ap.add_argument('--json-out')
    ap.add_argument('--report')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    if args.log:
        p = Path(args.log)
        if not p.exists():
            ap.error(f'日志不存在：{p}')
        text = p.read_text(encoding='utf-8', errors='replace')
    else:
        import sys
        text = sys.stdin.read()

    elf = Path(args.elf).resolve() if args.elf else None
    if elf and not elf.exists():
        ap.error(f'ELF 不存在：{elf}')
    result = analyze(text, elf, args.tool, args.tool_prefix)

    if args.json_out:
        p = Path(args.json_out); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.report:
        p = Path(args.report); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(render_markdown(result), encoding='utf-8')
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))


if __name__ == '__main__':
    main()
