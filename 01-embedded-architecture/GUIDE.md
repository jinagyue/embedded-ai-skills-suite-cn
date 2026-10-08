# 嵌入式软件架构

## 默认五层模型
```text
L5  App + RTOS任务编排       产品流程、状态机、任务入口
 ↓
L4  Service                 测量、存储、通信、电源、UI等业务能力
 ↓
L3  Device/Protocol/BSP服务  具体器件、协议、流式资源、板级资源绑定
 ↓
L2  BSP Driver              GPIO/UART/SPI/I2C/ADC/TIM/DMA/CAN
 ↓
L1  Vendor/CubeMX           CMSIS、HAL、LL、Startup、IRQ、生成初始化代码
```
横向层：`Middlewares/`、`Common/`、`Config/`、`Tests/`。

## 核心原则
- **目录名不等于职责**：先读实现，再给模块分层。
- **上层依赖下层，禁止反向 include**。
- APP 不直接调用 HAL；Service 尽量不直接知道 MCU 句柄。
- Protocol 负责“字节↔语义结构”，不负责产品流程。
- Device 表示具体器件，不等于 MCU 外设。
- 只抽象真实变化点；单板单 MCU 项目不要为了“高级”强加 Port/Manager/Factory。
- 架构结论必须有证据：include、调用、全局变量、HAL/RTOS API、资源所有权、构建目标。

## 机器化门禁
优先运行：
```bash
python tools/architecture_checker/architecture_checker.py . --evidence
python tools/architecture_checker/architecture_checker.py . --map arch-map.json --strict
python shared/scripts/include_graph.py .
python shared/scripts/hal_leak_check.py .
```

`arch-map.json` 用来记录“路径→语义角色”的人工确认结果。工具只复核依赖，不能替代架构判断。
