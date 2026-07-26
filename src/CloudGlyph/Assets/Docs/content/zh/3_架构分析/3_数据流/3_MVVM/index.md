# 数据流 — MVVM

## 命令执行流程

Execute(parameter) -> CanExecute 检查 -> 获取信号量 -> Started 事件 -> 异步执行 -> Completed/Failed 事件 -> 释放信号量 -> Exited 事件
