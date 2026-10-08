# 嵌入式开发总工作流

## 什么时候使用
当用户要求新建 STM32 工程、增加外设/协议/业务、重构旧工程、设计 FreeRTOS、排查 HardFault/复位/丢包/死锁，或要求 AI 自动构建与调试时使用。

## 固定流程
1. **工程发现**：识别 `.ioc`、MCU、构建系统、HAL/LL、FreeRTOS、FatFs/LVGL/lwIP、现有目录和固件产物。
2. **静态证据**：运行 `analyze_project.py`、`architecture_checker.py`、`hal_leak_check.py`、`stm32_resource_audit.py`。
3. **架构归类**：把代码映射到 L1~L5；目录名不能代替职责判断。
4. **FreeRTOS 设计**：按并发活动划 Task；决定 Queue/Mutex/Semaphore/Event/Notification。
5. **接口优先**：先写 `.h` 契约、数据所有权、错误码，再写实现。
6. **最小改动**：优先纵向切片，避免一次性重写整个项目。
7. **构建与固件分析**：编译成功后分析 ELF/Map，检查 Flash/RAM、符号和异常增长。
8. **动态调试**：串口/RTT/SWO/ITM/GDB 收集证据；默认禁止自动烧录。
9. **闭环复核**：修改后重新扫描、构建和观测，比较前后证据。

## 默认命令
```bash
python shared/scripts/analyze_project.py .
python shared/scripts/generate_arch_docs.py .
python tools/architecture_checker/architecture_checker.py . --map arch-map.json
python tools/elf_analyzer/elf_analyzer.py build/app.elf --all
python shared/scripts/auto_debug.py static --workspace .
```

## 输出要求
AI 在改代码之前应先给出：工程概况、当前模块归类、风险清单、目标架构、Task/IPC 设计、预计修改文件和验证方法。缺少证据时明确写“未验证”，不要把推测写成事实。
