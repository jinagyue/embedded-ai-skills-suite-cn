# 串口监控工具

依赖：`pip install pyserial`

```bash
python serial_monitor.py --list
python serial_monitor.py -p COM3 -b 115200 --mode both --log run.log
python serial_monitor.py -p COM3 -b 115200 --mode hex --duration 10 --jsonl evidence.jsonl --no-input
```

`--mode ascii|hex|both` 控制显示；`--duration` 适合 AI 自动调试中定时采证；`--jsonl` 生成结构化运行证据；默认自动重连。
