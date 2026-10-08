# Embeddedskills

这是一项技能，包含 12 个内部模块。根据当前任务只读取相关模块的 `GUIDE.md`，然后调用该模块的原始 Python 脚本；内部模块无需独立安装或注册。

## 选择模块

| 用户任务或工程类型 | 读取的说明 |
|---|---|
| Keil MDK/uVision，`.uvprojx`/`.uvproj`/`.uvmpw`，编译与 Target | [keil/GUIDE.md](keil/GUIDE.md) |
| CMake + ARM GCC，preset、构建、ELF 大小 | [gcc/GUIDE.md](gcc/GUIDE.md) |
| EIDE，`.eide/eide.yml`，配置与 unify_builder 构建 | [eide/GUIDE.md](eide/GUIDE.md) |
| J-Link，烧录、内存/寄存器、GDB、RTT/SWO | [jlink/GUIDE.md](jlink/GUIDE.md) |
| OpenOCD，ST-Link/CMSIS-DAP，烧录、GDB、Semihosting/ITM | [openocd/GUIDE.md](openocd/GUIDE.md) |
| 明确使用 probe-rs/cargo-embed，探针、烧录、GDB、RTT | [probe-rs/GUIDE.md](probe-rs/GUIDE.md) |
| UART/COM/AT，扫描、单次发送、监控与日志 | [serial/GUIDE.md](serial/GUIDE.md) |
| CAN/CAN-FD，报文、DBC、接口、总线统计 | [can/GUIDE.md](can/GUIDE.md) |
| 网络接口、tshark/Wireshark、pcap、ping、端口与流量 | [net/GUIDE.md](net/GUIDE.md) |
| 设备或服务器 SSH，单次命令、文件传输、隧道 | [ssh/GUIDE.md](ssh/GUIDE.md) |
| 需要保留会话状态的串口控制台、SSH Shell、本地交互程序 | [terminal/GUIDE.md](terminal/GUIDE.md) |
| 一键构建烧录、自动诊断、串联 build/flash/debug/observe | [workflow/GUIDE.md](workflow/GUIDE.md) |

尊重用户指定的工程和后端。信息不足时先读取相关配置、工程或候选列表；多个工程、Target、preset 或设备影响选择时再询问。仅编译的任务调用构建模块；需要多个阶段的任务再使用 workflow。使用 workflow 时也读取实际涉及的底层模块说明。

串口持续抓日志用 serial；需要反复发送命令并接着读取响应的控制台用 terminal；一次性远程命令用 ssh。GCC 模块只支持 CMake 型工程。

## 路径与执行

将本文件所在目录记为 `ROOT`。各说明中的 `<skill-dir>`、`skill/`、`{baseDir}` 和该模块的 `scripts/` 都指 `ROOT/<模块名>/`，而不是 `ROOT`。例如 Keil 脚本的绝对路径为 `ROOT/keil/scripts/keil_build.py`。说明提到其他 skill 时，读取这里对应模块的 `GUIDE.md`。

从用户目标工程目录运行脚本，脚本路径使用绝对路径；支持 `--workspace` 的脚本优先显式指定目标工程。保持工作目录在目标工程，避免把共享状态写到技能安装目录。Windows 使用当前 shell 的引号和参数语法。

先按模块说明检查实际需要的工具、驱动和 Python 依赖；命令参数不确定时读取该脚本的 `--help`。工具不存在时报告缺少的依赖，按用户请求的范围处理安装或配置。

模块环境配置保存在 `ROOT/<模块名>/config.json`；工程共享配置和状态仍保存在目标工程的 `.embeddedskills/config.json`、`.embeddedskills/state.json`。保持内部模块为同级目录，workflow 依赖这个布局查找构建和调试脚本。

只执行用户已授权的阶段；安装或调用总技能本身不授权烧录、擦除、发送测试帧或远程修改。已有授权继续有效，内部模块的默认操作模式不扩大请求范围。一次阶段失败时读取结构化错误和日志，停止依赖该阶段的后续操作。

按脚本 JSON、构建产物、日志和设备反馈报告结果，区分命令可加载、构建成功、烧录成功与硬件验证通过。

用户可用 `$embeddedskills` 显式调用，也可直接描述任务，例如“编译这个 Keil 工程”或“查看板子的串口日志”。模块名是内部路由，不是单独的技能入口。
