# 架构分层复核器

本工具采用“**先分析、后确认、再机器复核**”流程：

```bash
python architecture_checker.py . --evidence
cp arch-map.example.json ../../arch-map.json
# 阅读工程后修改 arch-map.json
python architecture_checker.py . --map arch-map.json --strict --json-out .embedded-ai/architecture_gate.json
```

`--evidence` 只收集事实，不下架构结论；`--strict` 在未分类、逆向依赖或 HAL 头泄漏时返回非 0，适合 CI/Hook。
