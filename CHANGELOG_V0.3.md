# V0.3 中文版更新记录

- 全部 `SKILL.md` 改为中文说明与中文工作流。
- 引入 JiaxI2/Codex-Skills 的嵌入式技能分流思想：C99、ARM、OS、Review、Architecture 分工更明确。
- 新增“语义判断先于工具”的 `arch-map.json` 架构门禁流程。
- 新增 `architecture_checker.py` 和 `skill_validator.py`。
- 新增增强版中文 `serial_monitor.py`：ASCII/HEX/BOTH、时间戳、日志、自动重连、限时采集、JSONL。
- 新增增强版中文 `elf_analyzer.py`：Section、Flash/RAM、最大函数/对象、JSON/Markdown 报告。
- 保留 V0.2 CubeMX/FreeRTOS/include/HAL/Pin-DMA-IRQ/Auto Debug 工具链和 zhinkgit/embeddedskills 桥接。
- 普通 STM32 项目默认不强制 `port_mcu`，只有真实跨 MCU/SDK 需求才引入。
