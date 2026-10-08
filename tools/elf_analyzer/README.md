# ELF 固件分析工具
依赖：`pip install pyelftools`

```bash
python elf_analyzer.py build/app.elf
python elf_analyzer.py build/app.elf --all --json-out elf.json --report ELF_REPORT.md
```

输出 ELF 架构、入口、Section、Flash/RAM 估算、最大函数和最大对象。`--json-out` 适合 AI/CI 做前后版本比较。
