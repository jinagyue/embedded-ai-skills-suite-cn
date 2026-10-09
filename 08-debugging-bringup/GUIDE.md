# 嵌入式调试与 Bring-up

![Bring-up · 逐层验证结构](../docs/assets/skills/08-debugging-bringup.png)

## 新板顺序
```text
电源/复位 → SWD → 时钟 → GPIO心跳 → 调试串口 → Timer/Tick
→ 单个外设 → DMA/IRQ → RTOS → Middleware → 完整业务
```
一次只增加一个复杂因素。

## 证据优先
优先拿到：复位原因、编译/链接日志、Fault 寄存器、PC/LR、串口时间戳日志、Task 栈水位、Queue 深度、IRQ 优先级、DMA 状态和示波器/逻辑分析仪波形。

## 串口工具
```bash
python tools/serial_monitor/serial_monitor.py --list
python tools/serial_monitor/serial_monitor.py -p COM3 -b 115200 --mode both --log run.log
```
串口监控支持 ASCII/HEX、时间戳、日志和自动重连，可直接作为 AI 自动调试的运行证据源。

## V0.4 Fault 闭环
```text
串口/RTT/GDB Fault日志
  ↓
HardFault Decoder
  ↓
CFSR/HFSR/BFAR/MMFAR + EXC_RETURN
  ↓
PC/LR
  ↓
addr2line + ELF
  ↓
源码文件:行号
  ↓
最小修复 + 重现验证
```

出现 HardFault 时，先保全证据，不要第一时间通过“加延时/清零变量/扩大所有栈”掩盖根因。
