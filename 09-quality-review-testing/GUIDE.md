# 嵌入式质量、评审与测试

![质量验证 · 测试层级结构](../docs/assets/skills/09-quality-review-testing.png)

## 评审顺序
1. 功能正确性与边界；2. ISR/并发；3. 内存和栈；4. 硬件资源；5. 错误处理；6. 架构依赖；7. 可测试性；8. 风格。

## 测试层级
- Host Unit Test：Protocol、算法、状态机、Common。
- Integration：Service + Fake Device/BSP。
- Target Test：真实 MCU 外设。
- HIL：实际板卡与仪器。
- Regression：每次修复都保留复现用例。

## 固件体积门禁
编译后运行：
```bash
python tools/elf_analyzer/elf_analyzer.py build/app.elf --all --json-out .embedded-ai/elf.json
```
比较 Flash/RAM、最大函数、最大对象和段增长，防止“功能正常但资源失控”。

Keil 工程同时分析 `.map`：
```bash
python tools/keil_map_analyzer/keil_map_analyzer.py build/app.map --json-out .embedded-ai/map.json --report .embedded-ai/MAP_REPORT.md
```
MAP 更适合追踪 armlink 的 Code/RO/RW/ZI、Execution Region 和对象文件贡献；ELF 更适合做通用 Section/符号分析。
