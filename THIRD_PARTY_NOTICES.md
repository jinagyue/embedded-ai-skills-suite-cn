# 第三方来源与许可说明

本套件吸收的是公开项目中的**方法、工作流思想和工具功能**；新增 Python 工具均为本套件重新实现，未直接复制第三方脚本正文。

## JiaxI2/Codex-Skills
- 来源：`https://github.com/JiaxI2/Codex-Skills`
- 许可证：Apache License 2.0
- 借鉴内容：中文优先的 embedded skill 路由、C99/ARM/OS/Review/Architecture 领域划分，以及 Architecture Skill 中“先语义分析→人工确认 arch-map→工具复核→CI 门禁”的设计方法。
- 本套件的 `architecture_checker.py` 是独立 Python 实现。

## shangliny10-lab/embedded-skills
- 来源：`https://github.com/shangliny10-lab/embedded-skills`
- 许可证：MIT
- 借鉴内容：`serial_monitor` 和 `elf_analyzer` 的功能范围。
- 本套件同名工具为重新实现，并增加适合 AI 自动调试的 JSON/限时采证能力。

## zhinkgit/embeddedskills
- 来源：`https://github.com/zhinkgit/embeddedskills`
- 许可证：MIT
- 上游 V0.2 起通过外部适配器调用其 Keil/GCC/EIDE + J-Link/OpenOCD/probe-rs 工作流。本单入口整合版随包提供 12 个工具后端，固定为提交 `536c1f929e359a5c02ef8ea9f1a20691e8d764e3`；原 MIT 许可证保存在 `third_party/embeddedskills-LICENSE`。

使用或再分发第三方原始代码时，应遵守各自许可证和 NOTICE/版权要求。

## GNU Arm Embedded Toolchain（可选外部工具）
- V0.4 的 `addr2line_resolver.py` / `hardfault_decoder.py` 可调用用户本机安装的 `arm-none-eabi-addr2line`。
- 本套件**不捆绑、不再分发** GNU Arm Embedded Toolchain 或其二进制文件；许可证以用户所安装工具链版本为准。

## FreeRTOS API
- `freertos_runtime_probe.c/.h` 是本套件原创的诊断探针示例，通过 FreeRTOS 公共 API（如 `uxTaskGetSystemState`、`uxTaskGetStackHighWaterMark`）采集运行时证据。
- 本套件不包含 FreeRTOS 内核源码。
