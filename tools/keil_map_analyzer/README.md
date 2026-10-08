# Keil `.map` 分析器

用于分析 MDK-ARM / Arm Linker 生成的 `.map` 文件，把固件占用转换为 AI 可读的 JSON/Markdown 证据。

```bash
python tools/keil_map_analyzer/keil_map_analyzer.py build/app.map \
  --json-out .embedded-ai/debug/keil_map.json \
  --report .embedded-ai/debug/KEIL_MAP_REPORT.md
```

重点输出：

- `Program Size`：Code / RO-data / RW-data / ZI-data；
- 估算 Flash = Code + RO + RW；
- 估算 RAM = RW + ZI；
- Execution Region / Load Region；
- Image component sizes；
- 最大函数、最大数据对象；
- Flash/RAM 占用最大的 `.o` / 库成员。

不同 armlink 版本的 map 文本格式会有差异。工具会尽力解析，无法识别的符号行会跳过，不会伪造结果。
