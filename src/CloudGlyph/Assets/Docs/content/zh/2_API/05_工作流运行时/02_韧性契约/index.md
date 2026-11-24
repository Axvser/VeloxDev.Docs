# 韧性契约

六项能力让宿主观测、暂停、恢复或回卷一次运行。每项都可选、都配置在 `RuntimeContext` 上，且都是旁路：一个都不配置时，运行行为与之前完全一致。

- [重定向与重试](00_重定向与重试/index.md) — 节点自己的回退决定，以及抛出失败的重试策略。
- [暂停门与观察者](01_暂停门与观察者/index.md) — 在节点之间暂停、运行时间线，以及可选的运行时通知。
- [错误接收与补偿](02_错误接收与补偿/index.md) — 作为记录的失败，以及失败运行已经做过的事。

所有类型都在 `VeloxDev.Core.WorkflowSystem.CompilerEx`。委托实现（`DelegateExecutionGate`、`DelegateExecutionObserver`、`DelegateExecutionErrorSink`、`DelegateExecutionCompensation`）是一行式写法；接口是扩展缝。

```csharp
var session = new RuntimeContext
{
    Data = "seed",
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3),
    Observer = new DelegateExecutionObserver(o => Console.WriteLine(o.Kind)),
    ErrorSink = new DelegateExecutionErrorSink(e => Console.WriteLine(e.Message)),
};
```
