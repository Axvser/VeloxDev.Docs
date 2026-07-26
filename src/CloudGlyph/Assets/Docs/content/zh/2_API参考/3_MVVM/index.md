# MVVM — API 参考

## 命名空间: VeloxDev.MVVM

### VeloxCommand

| 构造函数 | 描述 |
|---|---|
| VeloxCommand(Func<Task>) | 异步命令 |
| VeloxCommand(Action<object?>) | 同步命令带参数 |
| VeloxCommand(Func<object?, CancellationToken, Task>) | 完整异步带取消 |
| VeloxCommand(Func<object?, CancellationToken, Task>, Predicate<object?>, int) | 完整版 |

### 事件

| 事件 | 描述 |
|---|---|
| Started | 执行开始 |
| Completed | 执行成功 |
| Failed | 执行失败 |
| Canceled | 执行取消 |
| Exited | 生命周期结束 |
