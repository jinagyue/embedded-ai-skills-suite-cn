# 图件设计说明与提示词

模板：GPT-Image2 Style Library 的 **Infographic Engine / 信息图引擎**（`infographic-engine`，参考案例 334、1、8），采用技术图解方向。

最终图件由可复现的二维图形脚本生成，保留 SVG 文本、方框与连线，并导出 PNG。此文件的提示词是设计规范，最终图件没有调用图像生成模型。

生成源码与模块来源见 [docs/diagrams](diagrams/README.md)。中文字体与布局由脚本控制，避免模块名称或依赖箭头出现生成错误。

## 统一设计提示词

```text
根据给定技能文档绘制技术结构图或架构图。白色背景、二维方框、分组区域、正交箭头。
标注真实模块名称、职责、输入输出和关系。用蓝色表示控制或接口，绿色表示能力与结果，
紫色表示逻辑与编排，橙色表示硬件与异常路径，灰色表示配置与公共资源。
中文标签可读，技术术语保留原名。明确依赖、调用或数据流的方向，虚线表达可选路由或复核。
不添加立体芯片、光效、摄影素材、产品口号、装饰图案或未在文档中声明的功能。
输出可编辑 SVG 与 PNG。
```

## 嵌入式技能套件 · 单入口架构

依据：[SKILL.md](../SKILL.md)

```text
主题：嵌入式技能套件 · 单入口架构
任务与布局：任务按需路由到内部 GUIDE.md，再调用对应脚本；外部只注册一个 SKILL.md
结构节点：
- entry: embeddedskills / SKILL.md；用户任务 → 专业模块选择 → 工具后端选择
- p0: 设计与平台；00 总工作流；01 五层架构；02 C99 实现；03 Cortex-M
- p1: 外设与并发；04 STM32 / BSP；05 Device / Service；06 FreeRTOS / IPC；07 通信协议
- p2: 验证与演进；08 Bring-up / 调试；09 评审与测试；10 可靠性 / 低功耗；11 渐进重构
- p3: 证据与闭环；12 AI 自动调试；13 固件分析工具箱
- b0: 构建；Keil MDK；CMake / ARM GCC；EIDE
- b1: 下载与调试；J-Link；OpenOCD；probe-rs
- b2: 通信与连接；serial / CAN / net；SSH / terminal
- b3: 阶段编排；workflow；发现 → 选择 → 串联；聚合结果与状态
- data: 工程侧证据与状态；.embedded-ai/：分析报告      .embeddedskills/：配置 / 状态 / 执行日志
连接关系：
- embeddedskills / SKILL.md → 设计与平台
- embeddedskills / SKILL.md → 外设与并发
- embeddedskills / SKILL.md → 验证与演进
- embeddedskills / SKILL.md → 证据与闭环
- embeddedskills / SKILL.md → 构建，虚线
- embeddedskills / SKILL.md → 下载与调试，虚线
- embeddedskills / SKILL.md → 通信与连接，虚线
- embeddedskills / SKILL.md → 阶段编排，虚线
- 构建 → 工程侧证据与状态
- 下载与调试 → 工程侧证据与状态
- 通信与连接 → 工程侧证据与状态
- 阶段编排 → 工程侧证据与状态
图下注释：实线：专业路由与状态流。虚线：工具选用。专业模块给出方法，工具后端执行命令。
画布：1600 × 1360
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 嵌入式开发 · 总流程

依据：[00-embedded-workflow/GUIDE.md](../00-embedded-workflow/GUIDE.md)

```text
主题：嵌入式开发 · 总流程
任务与布局：从工程发现到运行证据，以可验证的纵向切片推进
结构节点：
- 0: 01 工程发现；.ioc / MCU / SDK / RTOS；工程目录与构建系统
- 1: 02 静态证据；工程扫描 / 资源审计；分层归类 / 依赖门禁
- 2: 03 设计契约；Task / IPC / 数据所有权；公共接口 / 错误码
- 3: 04 最小实现；先接口后实现；按纵向链路修改
- 4: 05 构建与分析；编译 / 链接；ELF / MAP / Flash / RAM
- 5: 06 采证与复核；串口 / RTT / GDB；比较修改前后的证据
连接关系：
- 01 工程发现 → 02 静态证据
- 02 静态证据 → 03 设计契约
- 03 设计契约 → 04 最小实现
- 04 最小实现 → 05 构建与分析
- 05 构建与分析 → 06 采证与复核
- 06 采证与复核 → 01 工程发现，虚线
图下注释：流程按本次任务范围裁剪；需要设备操作时执行已授权的阶段。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 嵌入式软件 · 五层架构

依据：[01-embedded-architecture/GUIDE.md](../01-embedded-architecture/GUIDE.md)

```text
主题：嵌入式软件 · 五层架构
任务与布局：箭头表示上层对下层的依赖；职责以实现与资源所有权为依据
结构节点：
- 0: L5  App + RTOS 任务编排；产品流程 / 状态机 / 任务入口
- 1: L4  Business Service；测量 / 存储 / 通信 / 电源 / UI 能力
- 2: L3  Device / Protocol / BSP Service；具体器件 / 协议语义 / 稳定数据通道
- 3: L2  BSP Driver；GPIO / UART / SPI / I2C / ADC / TIM / DMA / CAN
- 4: L1  Vendor / CubeMX；CMSIS / HAL / LL / Startup / IRQ / 生成初始化
- side: 横向公共资源；Middlewares/；Common/；Config/；Tests/；；复核：include / 调用；HAL 泄漏 / 构建目标
连接关系：
- L5  App + RTOS 任务编排 → L4  Business Service
- L4  Business Service → L3  Device / Protocol / BSP Service
- L3  Device / Protocol / BSP Service → L2  BSP Driver
- L2  BSP Driver → L1  Vendor / CubeMX
图下注释：APP 不直接调用 HAL；禁止反向 include；arch-map.json 记录人工确认的语义角色。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## C99 模块 · 接口与状态结构

依据：[02-c99-embedded/GUIDE.md](../02-c99-embedded/GUIDE.md)

```text
主题：C99 模块 · 接口与状态结构
任务与布局：公共契约与私有实现分开；调用者通过状态码接收结果
结构节点：
- caller: 调用者 / APP / Service；参数 / 长度 / 超时；明确缓冲区所有权
- api: module.h · 公共契约；固定宽度类型 / 配置结构；init / start / process / stop
- impl: module.c · 实现；参数与状态检查；错误传播 / 可重入约束
- state: 文件私有状态；static 状态 / 有界缓冲区；栈预算 / 资源生命周期
- result: mod_status_t；OK / EINVAL / EBUSY；ETIMEOUT / EIO
连接关系：
- 调用者 / APP / Service → module.h · 公共契约
- module.h · 公共契约 → module.c · 实现
- module.c · 实现 → 文件私有状态
- module.c · 实现 → mod_status_t
- mod_status_t → 调用者 / APP / Service
图下注释：volatile 不提供线程安全；并发访问需要明确的 IPC 或同步机制。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## Cortex-M · 启动与异常结构

依据：[03-arm-cortexm/GUIDE.md](../03-arm-cortexm/GUIDE.md)

```text
主题：Cortex-M · 启动与异常结构
任务与布局：启动链路、异常证据与 DMA / Cache 一致性三个关注面
结构节点：
- s0: Reset / 向量表；Reset_Handler 入口
- s1: 运行环境初始化；.data / .bss / SystemInit
- s2: main / Task / ISR；NVIC 优先级 / 延后处理
- fault: Fault 现场；PC / LR / xPSR / MSP / PSP；CFSR / HFSR / BFAR / MMFAR
- decode: 解码与符号定位；HardFault Decoder；addr2line + ELF → 源码行
- memory: 内存与外设一致性；栈边界 / MPU / Cache；DMA：对齐 / clean / invalidate
连接关系：
- Reset / 向量表 → 运行环境初始化
- 运行环境初始化 → main / Task / ISR
- main / Task / ISR → Fault 现场
- Fault 现场 → 解码与符号定位
图下注释：RTOS ISR API 受中断优先级约束；有 Cache 的平台需处理 DMA 缓冲区一致性。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## STM32 · 配置与 BSP 结构

依据：[04-stm32-platform/GUIDE.md](../04-stm32-platform/GUIDE.md)

```text
主题：STM32 · 配置与 BSP 结构
任务与布局：CubeMX 管理硬件配置；BSP 对上提供稳定板级 API
结构节点：
- ioc: .ioc / CubeMX；时钟 / PinMux / NVIC；DMA / 外设 / RTOS 配置
- vendor: 生成初始化 / HAL / LL；USER CODE 扩展点；MCU 句柄与厂商接口
- bsp: BSP Driver；GPIO / UART / SPI / I2C；ADC / TIM / DMA / CAN
- service: Device / Service / APP；使用稳定 BSP API；隐藏 HAL_* 与 MCU 句柄
- audit: 配置与源码一致性检查；parse_ioc / stm32_resource_audit；ioc_source_consistency：资源与配置漂移
连接关系：
- .ioc / CubeMX → 生成初始化 / HAL / LL（生成）
- BSP Driver → 生成初始化 / HAL / LL（封装）
- Device / Service / APP → BSP Driver
- .ioc / CubeMX → 配置与源码一致性检查
- 生成初始化 / HAL / LL → 配置与源码一致性检查
图下注释：.ioc 与源码双向复核 GPIO / NVIC / DMA / RTOS，检查配置漂移。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## Device / Protocol / Service · 职责结构

依据：[05-device-service/GUIDE.md](../05-device-service/GUIDE.md)

```text
主题：Device / Protocol / Service · 职责结构
任务与布局：业务能力、器件控制、字节语义与数据通道分开
结构节点：
- app: APP / 产品流程；
- business: Business Service；measurement_start / get_result
- device: Device · 具体器件；传感器 / Flash / 显示屏；寄存器与器件行为
- protocol: Protocol · 语义转换；帧格式 / CRC / 命令码；编码 / 解码 / 边界检查
- stream: BSP Service · 数据通道；UART + DMA + IDLE；ringbuffer + notification
- bsp: BSP Driver；稳定板级 API → HAL / LL → MCU 外设
连接关系：
- APP / 产品流程 → Business Service
- Business Service → Device · 具体器件
- Business Service → Protocol · 语义转换
- Business Service → BSP Service · 数据通道
- Device · 具体器件 → BSP Driver
- BSP Service · 数据通道 → BSP Driver
图下注释：Protocol 负责字节与语义转换；APP 使用业务能力接口，不感知具体 HAL 句柄。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## FreeRTOS · Task 与 IPC 结构

依据：[06-freertos-design/GUIDE.md](../06-freertos-design/GUIDE.md)

```text
主题：FreeRTOS · Task 与 IPC 结构
任务与布局：按独立并发活动划分 Task；每条连线标明交互机制
结构节点：
- isr: ISR / 外设事件；采样 / 清标志 / 时间戳；非阻塞投递事件
- comm: CommTask；接收 / 协议解析；命令分发
- measure: MeasureTask；采集与计算；测量结果
- storage: StorageTask / UITask；存储 / 显示；结果消费
- timer: Software Timer；周期事件；通知 Task
- shared: 共享 SPI / UART 资源；以 Mutex 串行化访问
- health: HealthTask / 运行探针；活性 / Stack HWM / Heap；运行时记录 → 分析报告
连接关系：
- ISR / 外设事件 → CommTask（Notification）
- CommTask → MeasureTask（Queue）
- MeasureTask → StorageTask / UITask（Queue）
- Software Timer → MeasureTask（Notification）
- MeasureTask → 共享 SPI / UART 资源
- StorageTask / UITask → 共享 SPI / UART 资源
- CommTask → HealthTask / 运行探针，虚线
- MeasureTask → HealthTask / 运行探针，虚线
- StorageTask / UITask → HealthTask / 运行探针，虚线
图下注释：示例关系用于任务设计；具体 Task 数量、优先级与栈预算由目标工程确定。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 嵌入式通信 · 分层链路

依据：[07-embedded-protocols/GUIDE.md](../07-embedded-protocols/GUIDE.md)

```text
主题：嵌入式通信 · 分层链路
任务与布局：发送方向自上而下；接收方向自下而上，Protocol 完成字节与语义转换
结构节点：
- 0: APP / Service；语义命令 / 业务结果
- 1: Protocol；帧界定 / 长度 / CRC / 字节序 / 重同步
- 2: BSP Service / Link；字节流 / 消息 / 环形缓冲区
- 3: BSP Driver；驱动 API / HAL 封装
- 4: UART / CAN / SPI / I2C / USB；MCU 通信外设
- side: UART 接收示例；DMA + IDLE；↓；环形 / 双缓冲；↓；Task 通知；↓；Protocol parser
连接关系：
- APP / Service → Protocol
- Protocol → BSP Service / Link
- BSP Service / Link → BSP Driver
- BSP Driver → UART / CAN / SPI / I2C / USB
图下注释：接收回调仅记录数据段并通知 Task；协议必须处理超时、缓存上限和异常输入。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## Bring-up · 逐层验证结构

依据：[08-debugging-bringup/GUIDE.md](../08-debugging-bringup/GUIDE.md)

```text
主题：Bring-up · 逐层验证结构
任务与布局：一次增加一个复杂因素，以基础硬件为起点
结构节点：
- 0: 01 基础硬件；电源 / 复位 / SWD；连接与复位原因
- 1: 02 最小运行；时钟 / GPIO 心跳；调试串口 / Tick
- 2: 03 外设与中断；单个外设；DMA / IRQ
- 3: 04 并发与中间件；RTOS / Middleware；完整业务
- 4: 05 运行证据；日志 / 栈水位 / Queue；IRQ / DMA / 波形
- 5: 06 Fault 定位；寄存器 → PC / LR；ELF + addr2line → 源码
连接关系：
- 01 基础硬件 → 02 最小运行
- 02 最小运行 → 03 外设与中断
- 03 外设与中断 → 04 并发与中间件
- 04 并发与中间件 → 05 运行证据
- 05 运行证据 → 06 Fault 定位
- 06 Fault 定位 → 01 基础硬件，虚线
图下注释：异常定位后保全证据，再做最小修复与重现验证。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 质量验证 · 测试层级结构

依据：[09-quality-review-testing/GUIDE.md](../09-quality-review-testing/GUIDE.md)

```text
主题：质量验证 · 测试层级结构
任务与布局：测试范围从纯逻辑扩展到真实外设与系统环境
结构节点：
- 0: Host Unit Test；Protocol / 算法 / 状态机 / Common
- 1: Integration；Service + Fake Device / BSP
- 2: Target Test；真实 MCU 外设
- 3: HIL；实际板卡与仪器
- 4: Regression；保存复现用例，持续比较修复前后行为
- side: 跨阶段评审与门禁；功能与边界 / 并发；内存 / 栈 / 硬件资源；错误处理 / 架构依赖；；构建后：ELF / MAP；Flash / RAM / 段增长；最大函数 / 最大对象
连接关系：
- Host Unit Test → Integration
- Integration → Target Test
- Target Test → HIL
- HIL → Regression
图下注释：层级之间表示验证范围扩展；图中并不声明已完成目标工程的各级测试。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 可靠性与低功耗 · 状态结构

依据：[10-reliability-lowpower/GUIDE.md](../10-reliability-lowpower/GUIDE.md)

```text
主题：可靠性与低功耗 · 状态结构
任务与布局：将失败显式建模；由健康任务统一管理看门狗
结构节点：
- 0: INIT；
- 1: ONLINE；
- 2: DEGRADED；
- 3: OFFLINE；
- 4: RECOVERING；
- tasks: 关键 Task 活性证明；计数 / 时间戳 / 完成信号
- health: HealthTask；汇总关键任务状态；符合健康条件才喂狗
- watch: Watchdog；系统停滞 → 复位；记录复位原因
- power: 电源状态与恢复路径；RUN / SLEEP / STOP / OFF；资源状态 + 唤醒源 → 时钟恢复 → 外设重新校验
连接关系：
- INIT → ONLINE
- ONLINE → DEGRADED
- DEGRADED → OFFLINE
- OFFLINE → RECOVERING
- RECOVERING → ONLINE，虚线
- 关键 Task 活性证明 → HealthTask
- HealthTask → Watchdog
图下注释：唤醒后恢复时钟并复核外设；超时、降级与恢复条件由目标系统明确规定。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 存量工程 · 渐进重构路径

依据：[11-refactor-existing/GUIDE.md](../11-refactor-existing/GUIDE.md)

```text
主题：存量工程 · 渐进重构路径
任务与布局：每次迁移一条可验证纵向链路，保留旧路径与回退点
结构节点：
- 0: 01 现状盘点；职责 / 调用 / HAL / RTOS；共享状态与目标层
- 1: 02 抽出 Protocol；纯 parser / 帧与语义；保留协议复现用例
- 2: 03 抽出 Service；业务能力与错误路径；Task 调用能力接口
- 3: 04 封装 BSP / Device；板级资源 / 具体器件；稳定 API 隔离句柄
- 4: 05 整理 Task 与状态；等待事件 / 调用 APP；消除可写 extern
- 5: 06 门禁与回归；扫描 / 构建 / 测试；验证后调整目录
连接关系：
- 01 现状盘点 → 02 抽出 Protocol
- 02 抽出 Protocol → 03 抽出 Service
- 03 抽出 Service → 04 封装 BSP / Device
- 04 封装 BSP / Device → 05 整理 Task 与状态
- 05 整理 Task 与状态 → 06 门禁与回归
- 06 门禁与回归 → 01 现状盘点，虚线
图下注释：循环箭头：每个迁移步骤都复核行为与依赖，再进入下一条链路。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## AI 自动调试 · 证据闭环

依据：[12-auto-debug/GUIDE.md](../12-auto-debug/GUIDE.md)

```text
主题：AI 自动调试 · 证据闭环
任务与布局：先建立证据，再定位与最小修改；每次修复返回构建与采证
结构节点：
- 0: 01 静态工程模型；源码 / .ioc / 分层 / RTOS；GPIO / IRQ / DMA 一致性
- 1: 02 构建与固件分析；Build → MAP / ELF；Flash / RAM / 符号
- 2: 03 可选设备阶段；按任务选择 Flash / Debug；串口 / RTT / GDB 采证
- 3: 04 运行时分析；Task / Stack HWM / Heap；日志与异常记录
- 4: 05 故障定位；Fault 寄存器 / PC / LR；addr2line + ELF → 源码
- 5: 06 最小修改与复核；AI 修改 → 重新构建；重新采证 / 比较差异
连接关系：
- 01 静态工程模型 → 02 构建与固件分析
- 02 构建与固件分析 → 03 可选设备阶段
- 03 可选设备阶段 → 04 运行时分析
- 04 运行时分析 → 05 故障定位
- 05 故障定位 → 06 最小修改与复核
- 06 最小修改与复核 → 01 静态工程模型，虚线
图下注释：默认不自动烧录；循环中的设备阶段仅按任务授权与可用证据执行。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 固件工具箱 · 输入与分析结构

依据：[13-firmware-tools/GUIDE.md](../13-firmware-tools/GUIDE.md)

```text
主题：固件工具箱 · 输入与分析结构
任务与布局：工具围绕三类证据工作：静态工程、构建产物、运行记录
结构节点：
- in0: 工程源码 / .ioc；目录 / include / 外设配置
- tool0: 静态扫描与门禁；工程 / 架构 / HAL 泄漏；Pin / DMA / IRQ / RTOS；配置与源码一致性
- out0: 工程模型 / 架构报告；资源映射 / 依赖关系
- in1: MAP / ELF；段 / region / 符号 / 地址
- tool1: 固件产物分析；Keil MAP Analyzer；ELF Analyzer；addr2line Resolver
- out1: 资源与源码定位；Flash / RAM / 最大符号
- in2: 串口 / RTT / Fault 日志；运行快照 / 寄存器 / PC
- tool2: 运行记录分析；Serial Monitor；FreeRTOS Runtime Analyzer；HardFault Decoder
- out2: 运行与异常报告；Task / 栈堆 / Fault / 源码行
连接关系：
- 工程源码 / .ioc → 静态扫描与门禁
- 静态扫描与门禁 → 工程模型 / 架构报告
- MAP / ELF → 固件产物分析
- 固件产物分析 → 资源与源码定位
- 串口 / RTT / Fault 日志 → 运行记录分析
- 运行记录分析 → 运行与异常报告
图下注释：分析结果供架构与故障判断使用；硬件结论仍需对应的运行或测量证据。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## Keil MDK · 构建后端结构

依据：[keil/GUIDE.md](../keil/GUIDE.md)

```text
主题：Keil MDK · 构建后端结构
任务与布局：工程发现、配置选择、构建执行与产物记录的调用结构
结构节点：
- source: .uvprojx / .uvproj / .uvmpw；工程文件 / Target
- select: 工程与目标选择；CLI / config / state；scan + 目标枚举
- exec: UV4.exe / Keil 工具链；build / rebuild / clean
- result: 构建结果与日志；错误 / 警告 / 日志；AXF / HEX / BIN 等产物路径
- state: .embeddedskills/；config.json：已选参数；state.json：产物与执行状态
- next: 后续分析 / 工具调用；ELF / MAP / size；由 workflow 选择后续阶段
连接关系：
- .uvprojx / .uvproj / .uvmpw → 工程与目标选择
- 工程与目标选择 → UV4.exe / Keil 工具链
- UV4.exe / Keil 工具链 → 构建结果与日志
- 构建结果与日志 → .embeddedskills/
- .embeddedskills/ → 后续分析 / 工具调用
图下注释：图示为后端能力结构；图中工具路径与构建产物由本机环境和目标工程确定。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## CMake / ARM GCC · 构建结构

依据：[gcc/GUIDE.md](../gcc/GUIDE.md)

```text
主题：CMake / ARM GCC · 构建结构
任务与布局：工程发现、配置选择、构建执行与产物记录的调用结构
结构节点：
- source: CMake 工程；CMakeLists / Presets；当前支持 CMake 型工程
- select: 工程与目标选择；CLI / config / state；scan + 目标枚举
- exec: CMake + arm-none-eabi-gcc；configure → build；rebuild / clean / size
- result: 构建结果与日志；ELF / 构建日志；text / data / bss
- state: .embeddedskills/；config.json：已选参数；state.json：产物与执行状态
- next: 后续分析 / 工具调用；ELF / MAP / size；由 workflow 选择后续阶段
连接关系：
- CMake 工程 → 工程与目标选择
- 工程与目标选择 → CMake + arm-none-eabi-gcc
- CMake + arm-none-eabi-gcc → 构建结果与日志
- 构建结果与日志 → .embeddedskills/
- .embeddedskills/ → 后续分析 / 工具调用
图下注释：图示为后端能力结构；图中工具路径与构建产物由本机环境和目标工程确定。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## EIDE · 构建后端结构

依据：[eide/GUIDE.md](../eide/GUIDE.md)

```text
主题：EIDE · 构建后端结构
任务与布局：工程发现、配置选择、构建执行与产物记录的调用结构
结构节点：
- source: .eide/eide.yml；工程发现 / 配置枚举；ConfigName / builder.params
- select: 工程与目标选择；CLI / config / state；scan + 目标枚举
- exec: unify_builder；ARM CC (AC5 / AC6) 或 GCC；build / rebuild / clean / size
- result: 构建结果与日志；ELF / HEX / 日志；结构化结果与产物路径
- state: .embeddedskills/；config.json：已选参数；state.json：产物与执行状态
- next: 后续分析 / 工具调用；ELF / MAP / size；由 workflow 选择后续阶段
连接关系：
- .eide/eide.yml → 工程与目标选择
- 工程与目标选择 → unify_builder
- unify_builder → 构建结果与日志
- 构建结果与日志 → .embeddedskills/
- .embeddedskills/ → 后续分析 / 工具调用
图下注释：图示为后端能力结构；图中工具路径与构建产物由本机环境和目标工程确定。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## J-Link · 下载与调试结构

依据：[jlink/GUIDE.md](../jlink/GUIDE.md)

```text
主题：J-Link · 下载与调试结构
任务与布局：主机包装脚本通过调试后端访问目标 MCU，聚合执行结果与观测数据
结构节点：
- input: 目标与输入；芯片 / 探针 / 接口 / 地址；HEX / BIN / ELF
- wrap: Python 后端脚本；参数解析 / 子进程调用；统一 JSON 与日志
- engine: J-Link Commander / Server；下载 / 读内存 / 执行控制
- target: 探针 → 目标 MCU；SWD / JTAG；Flash / RAM / CPU 寄存器
- observe: 观测与源码调试；GDB：backtrace / locals；RTT / 外部 SWO viewer
- report: 诊断结果；寄存器 / 内存 / backtrace；运行日志与阶段状态
连接关系：
- 目标与输入 → Python 后端脚本
- Python 后端脚本 → J-Link Commander / Server
- J-Link Commander / Server → 探针 → 目标 MCU
- 探针 → 目标 MCU → 观测与源码调试
- 观测与源码调试 → 诊断结果
图下注释：下载、复位、写内存等设备动作按本次任务选择；图中不表示已连接或验证设备。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## OpenOCD · 下载与调试结构

依据：[openocd/GUIDE.md](../openocd/GUIDE.md)

```text
主题：OpenOCD · 下载与调试结构
任务与布局：主机包装脚本通过调试后端访问目标 MCU，聚合执行结果与观测数据
结构节点：
- input: 目标与输入；芯片 / 探针 / 接口 / 地址；固件文件 / interface + target
- wrap: Python 后端脚本；参数解析 / 子进程调用；统一 JSON 与日志
- engine: OpenOCD / GDB Server；下载 / 读内存 / 执行控制
- target: 探针 → 目标 MCU；调试适配器 / 目标配置；Flash / RAM / CPU 寄存器
- observe: 观测与源码调试；GDB / 寄存器 / 断点；semihosting / ITM
- report: 诊断结果；寄存器 / 内存 / backtrace；运行日志与阶段状态
连接关系：
- 目标与输入 → Python 后端脚本
- Python 后端脚本 → OpenOCD / GDB Server
- OpenOCD / GDB Server → 探针 → 目标 MCU
- 探针 → 目标 MCU → 观测与源码调试
- 观测与源码调试 → 诊断结果
图下注释：下载、复位、写内存等设备动作按本次任务选择；图中不表示已连接或验证设备。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## probe-rs · 探针与调试结构

依据：[probe-rs/GUIDE.md](../probe-rs/GUIDE.md)

```text
主题：probe-rs · 探针与调试结构
任务与布局：主机包装脚本通过调试后端访问目标 MCU，聚合执行结果与观测数据
结构节点：
- input: 目标与输入；芯片 / 探针 / 接口 / 地址；ELF / HEX / BIN / UF2
- wrap: Python 后端脚本；参数解析 / 子进程调用；统一 JSON 与日志
- engine: probe-rs CLI / GDB；下载 / 读内存 / 执行控制
- target: 探针 → 目标 MCU；支持的调试探针 / 目标芯片；Flash / RAM / CPU 寄存器
- observe: 观测与源码调试；attach / run / GDB；RTT 日志
- report: 诊断结果；寄存器 / 内存 / backtrace；运行日志与阶段状态
连接关系：
- 目标与输入 → Python 后端脚本
- Python 后端脚本 → probe-rs CLI / GDB
- probe-rs CLI / GDB → 探针 → 目标 MCU
- 探针 → 目标 MCU → 观测与源码调试
- 观测与源码调试 → 诊断结果
图下注释：下载、复位、写内存等设备动作按本次任务选择；图中不表示已连接或验证设备。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 串口后端 · 收发与日志结构

依据：[serial/GUIDE.md](../serial/GUIDE.md)

```text
主题：串口后端 · 收发与日志结构
任务与布局：pyserial 接入 UART；读取、发送、日志和可选多路复用分开
结构节点：
- config: 端口与链路配置；scan / COM / 波特率；数据位 / 校验位 / 超时
- serial: pyserial / 串口连接；主机串口句柄；端口读写与生命周期
- board: USB-UART ↔ MCU；UART TX / RX；文本与二进制字节
- read: 接收与监控；monitor / hex；文本或 HEX 输出
- log: 日志与可选多路复用；log → 文件；mux → 多客户端读取
- send: 发送入口；send：文本 / Hex；返回实际发送结果
连接关系：
- 端口与链路配置 → pyserial / 串口连接
- pyserial / 串口连接 → USB-UART ↔ MCU
- pyserial / 串口连接 → 接收与监控
- pyserial / 串口连接 → 日志与可选多路复用
- 发送入口 → USB-UART ↔ MCU
图下注释：串口采集后端用于数据与证据收集；持续命令会话可使用 terminal 后端。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## CAN / CAN-FD · 总线工具结构

依据：[can/GUIDE.md](../can/GUIDE.md)

```text
主题：CAN / CAN-FD · 总线工具结构
任务与布局：适配器接入总线；收帧、发送、解码与统计构成独立能力
结构节点：
- config: 接口 / 通道 / 比特率；scan → 可用接口；PCAN / Vector / slcan 等
- pythoncan: python-can / 设备驱动；统一 CAN 帧接口；适配器连接
- bus: CAN / CAN-FD 总线；ID / DLC / Data / Flags；标准 / 扩展 / FD 帧
- recv: monitor / log / stats；报文监控 / ASC / BLF / CSV；负载 / ID 分布 / 帧率
- decode: decode + 数据库；DBC / ARXML 等；cantools → 信号值
- send: send；标准 / 扩展 / 远程 / FD 帧；单次 / 周期发送
连接关系：
- 接口 / 通道 / 比特率 → python-can / 设备驱动
- python-can / 设备驱动 → CAN / CAN-FD 总线
- python-can / 设备驱动 → monitor / log / stats
- monitor / log / stats → decode + 数据库
- send → CAN / CAN-FD 总线
图下注释：仲裁域与数据域速率、通道及 FD 模式由目标网络配置确定。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 网络后端 · 抓包与分析结构

依据：[net/GUIDE.md](../net/GUIDE.md)

```text
主题：网络后端 · 抓包与分析结构
任务与布局：在线抓包与离线分析分开；连通性检测是并行诊断能力
结构节点：
- iface: iface / 网络接口；目标 / 过滤器 / 时长；主机 ↔ 嵌入式设备
- capture: capture / tshark / dumpcap；抓包接口 / Npcap 等；采集网络帧
- pcap: PCAP / PCAPNG；保存采集文件；也可输入已有抓包文件
- analyze: 离线分析与统计；tshark / capinfos；协议 / 会话 / 流量
- summary: 结构化网络证据；JSON / 日志；定位链路与协议问题
- connect: 并行连通性诊断；ping / traceroute / 端口；系统网络工具
连接关系：
- iface / 网络接口 → capture / tshark / dumpcap
- capture / tshark / dumpcap → PCAP / PCAPNG
- PCAP / PCAPNG → 离线分析与统计
- 离线分析与统计 → 结构化网络证据
- 并行连通性诊断 → 结构化网络证据
图下注释：抓包依赖接口选择与抓包驱动；统计结果由实际采集的 PCAP / PCAPNG 产生。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## SSH · 远程操作网关结构

依据：[ssh/GUIDE.md](../ssh/GUIDE.md)

```text
主题：SSH · 远程操作网关结构
任务与布局：标准 OpenSSH 配置提供 Host 别名、认证与跳板信息
结构节点：
- host: Host 别名 / SSH config；HostName / User / Port；密钥 / ProxyJump
- resolve: ssh_config / 目标解析；list / find / resolve / show；确定唯一远端
- remote: OpenSSH ↔ 远程设备；身份认证 / 连接；Linux 开发板或服务器
- exec: ssh_exec / ssh_probe；远程命令 / 固定只读探测；标准输出 / 退出码
- transfer: ssh_transfer；SCP 上传 / 下载；本地与远端文件路径
- tunnel: ssh_tunnel；本地端口转发；本地端口 ↔ 远端服务
连接关系：
- Host 别名 / SSH config → ssh_config / 目标解析
- ssh_config / 目标解析 → OpenSSH ↔ 远程设备
- OpenSSH ↔ 远程设备 → ssh_exec / ssh_probe
- OpenSSH ↔ 远程设备 → ssh_transfer
- OpenSSH ↔ 远程设备 → ssh_tunnel
图下注释：持续交互 Shell 使用 terminal；本后端提供命令、传输、探测与隧道入口。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## 交互终端 · 会话结构

依据：[terminal/GUIDE.md](../terminal/GUIDE.md)

```text
主题：交互终端 · 会话结构
任务与布局：后台会话保存连接状态；send 与 read 组成持续的命令 / 响应交互
结构节点：
- cli: terminal_session.py；start / send / read / attach；list / status / stop
- session: 后台会话与输出缓冲；会话 ID / 名称 / 连接状态；持续读取远端输出
- state: .embeddedskills/state.json；会话状态记录；状态查询 / 生命周期
- serial: serial 后端；pyserial → MCU UART；AT / 控制台 / Bootloader
- ssh: ssh 后端；OpenSSH → 远端 Shell；持续命令与响应
- local: local 后端；Python 标准库；本机 Shell / REPL / CLI
连接关系：
- terminal_session.py → 后台会话与输出缓冲（命令 / 数据）
- 后台会话与输出缓冲 → .embeddedskills/state.json
- 后台会话与输出缓冲 → serial 后端
- 后台会话与输出缓冲 → ssh 后端
- 后台会话与输出缓冲 → local 后端
图下注释：read 读取并清空输出缓冲；stop 停止会话并清理状态。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```

## Workflow · 后端编排结构

依据：[workflow/GUIDE.md](../workflow/GUIDE.md)

```text
主题：Workflow · 后端编排结构
任务与布局：发现、选择、串联与聚合；通过子进程复用已有后端
结构节点：
- config: 配置与阶段请求；CLI → preferred_* → 自动发现；.embeddedskills/config.json
- plan: workflow_plan / workflow_run；plan / build / build-flash；build-debug / observe；diagnose
- state: 执行结果与 state.json；阶段状态 / 产物路径；聚合底层结构化错误
- build: 构建后端；Keil / GCC / EIDE；成功后产生固件路径
- probe: 下载 / 调试后端；J-Link / OpenOCD / probe-rs；按阶段请求选择
- observe: 观测候选；J-Link RTT / SWO；OpenOCD semihosting / ITM；probe-rs RTT
- result: 阶段串联边界；构建失败停止后续设备阶段；单次构建直接使用对应后端即可。
连接关系：
- 配置与阶段请求 → workflow_plan / workflow_run
- workflow_plan / workflow_run → 执行结果与 state.json
- workflow_plan / workflow_run → 构建后端
- workflow_plan / workflow_run → 下载 / 调试后端
- workflow_plan / workflow_run → 观测候选
- 构建后端 → 下载 / 调试后端（固件路径）
图下注释：observe 生成推荐观测命令；编排器内部不长时间占用观测通道。
画布：1600 × 1000
风格：白底二维技术图解；清晰中文标签；不使用海报元素。
```
