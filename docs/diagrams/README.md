# 可复现结构图源

27 张图由 `generate_diagrams.py` 中的节点、分组、坐标与连接关系生成；`specs.json` 是同一图源的结构化导出，供审阅使用。修改图件时编辑生成脚本中的相应 `Diagram`，再重新生成，避免手工改图与源数据不一致。

输出目录为 `docs/assets/skills/`，每个模块包含同名 SVG 和 PNG。SVG 保留可编辑文字、方框、线条与箭头，可在支持 SVG 的编辑器中继续修改。

重新生成仅需要 Python、Pillow 和中文字体；已生成的图件可以直接浏览，技能运行不依赖 Pillow。

```console
python -m pip install -r docs/diagrams/requirements.txt
python -X utf8 docs/diagrams/generate_diagrams.py
```

Windows 默认使用微软雅黑。其他环境默认尝试 Noto Sans CJK 或 PingFang；也可以通过 `DIAGRAM_FONT` 和 `DIAGRAM_FONT_BOLD` 指定 TTF/TTC 字体路径。SVG 在查看端使用字体回退，PNG 已固定渲染结果。

图源依据根 `SKILL.md` 与各模块 `GUIDE.md`。总入口展示包的实际单入口结构；专业模块展示推荐架构、流程或示例关系；后端展示文档支持的调用能力。生成图件不执行设备操作。
