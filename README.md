# 嵌入式 AI Skills 中文套件：单入口整合版

![嵌入式技能套件单入口架构](docs/assets/skills/embeddedskills.png)

面向 STM32、ARM Cortex-M、FreeRTOS/CMSIS-RTOS2 的开发与调试技能。基于 V0.4 中文套件整合，**外部只注册 `embeddedskills` 一个技能入口**，内部按需读取 14 个专业模块和 12 个工具后端。

专业模块覆盖架构、C99、CubeMX/外设、协议、FreeRTOS、重构、可靠性、静态分析、MAP/ELF、HardFault 和运行时日志。工具后端提供 Keil/EIDE/CMake ARM GCC、J-Link/OpenOCD/probe-rs、串口、CAN、网络和 SSH/交互终端。

[查看全部 27 张结构图与架构图](docs/SKILL_GALLERY.md) · [查看图件设计说明与提示词](docs/IMAGE_PROMPTS.md)

## 安装

将仓库完整目录安装为 Codex 技能目录中的 `embeddedskills/`，保留所有子目录。**只保留根目录的 `SKILL.md`**；内部 `GUIDE.md` 是按需读取的资源。已有同名版本时先备份，再替换。

安装 Python 核心依赖：

```console
python -m pip install -r requirements-tools.txt
```

EIDE 与 CAN 的 Python 依赖按需安装：

```console
python -m pip install -r requirements-backends-optional.txt
```

工具链、调试器软件和驱动详见 [依赖说明](docs/DEPENDENCIES.md)。

## 使用

在 Codex 中使用 `$embeddedskills`，或者直接提出任务：

- “检查这个 STM32 工程的 .ioc 与源码是否一致。”
- “分析这个 ELF/MAP 的 Flash 和 RAM 占用。”
- “解码 HardFault 日志并定位到源码行。”
- “编译这个 Keil 工程，输出编译结果。”
- “设计 FreeRTOS Task 和 IPC，再按指定范围修改。”

[总入口](SKILL.md) 路由到需要的说明；[工具后端](BACKENDS.md) 复用随包提供的脚本。专业说明中的脚本以仓库根为基准，后端说明中的 `scripts/` 以该后端目录为基准。调用脚本使用绝对路径，工作目录为目标工程。

套件使用工程的 `.embedded-ai/` 保存扫描和调试报告，工具后端使用 `.embeddedskills/` 保存工程配置和状态。默认不自动烧录，设备操作按用户请求的阶段执行。

## 结构

```text
embeddedskills/
  SKILL.md                    唯一技能入口
  00-embedded-workflow/        专业模块 GUIDE.md
  ...
  13-firmware-tools/
  keil/ gcc/ eide/ ...         工具后端 GUIDE.md 与 scripts/
  shared/                     扫描、编排脚本与模板
  tools/                      固件、Fault 与 RTOS 工具
  docs/                       架构、依赖与上游资料
  tests/                      示例与模拟自检
  third_party/                工具后端许可证
```

原套件的详细介绍保存在 [UPSTREAM_README.md](docs/UPSTREAM_README.md)，旧的多技能安装表述由本仓库的单入口结构替代。

## 验证

```console
python -X utf8 tests/run_smoke_tests.py
python -X utf8 tests/test_single_entry_packaging.py
python shared/scripts/check_dependencies.py --json
```

Smoke tests 使用示例 STM32 工程、模拟日志和命令发射器，验证静态扫描、MAP、Fault、RTOS 分析和流程串联。测试不连接设备，不能作为真实固件构建、烧录或硬件性能验证。

## 来源与再分发

本整合版保留 V0.4 套件的来源说明和历史文件，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。工具后端来自 [zhinkgit/embeddedskills](https://github.com/zhinkgit/embeddedskills)，固定为提交 `536c1f929e359a5c02ef8ea9f1a20691e8d764e3`，MIT 许可证保存在 [third_party/embeddedskills-LICENSE](third_party/embeddedskills-LICENSE)。

原 V0.4 压缩包未声明覆盖整套原创内容的总许可证，本整合版未替原作者新增许可。第三方组件沿用各自许可。
