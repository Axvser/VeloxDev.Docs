# 工作流运行时

`RuntimeEngine.RunAsync` 驱动 `CompiledGraph`。它遍历每个段，调用节点的 `ReceiveAsync`，并把返回值写回会话供下一节点使用。图决定形状，引擎决定路径、载荷与运行如何结束。

分析分为两个操作：

- [执行循环](00_执行循环/index.md) — `RunAsync`、段分派、节点驱动、汇合与重定向。
- [韧性与检查点](01_韧性与检查点/index.md) — 暂停门、重试、观察者、错误汇、补偿、检查点与日志写入器。

```csharp
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
Console.WriteLine($"{session.Status} {session.Outcome} {session.Data}");
```

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。
