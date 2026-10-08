# 可靠性与低功耗

## 失败应该成为状态
```text
INIT → ONLINE → DEGRADED → OFFLINE → RECOVERING
```
外设初始化必须有 timeout，不得无限循环并持续喂狗。

## Watchdog
由低优先级健康任务汇总关键 Task 的“活性证明”后统一喂狗。不要在定时器 ISR 或卡死循环中无条件喂狗，否则会掩盖系统停滞。

## 低功耗
明确 RUN/SLEEP/STOP/OFF 的资源状态、唤醒源、时钟恢复和外设重新校验。唤醒后不要默认外设仍处于可信状态。
