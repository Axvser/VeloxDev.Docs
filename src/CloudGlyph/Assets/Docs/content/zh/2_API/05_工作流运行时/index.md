# 工作流运行时

`RuntimeEngine.RunAsync` 驱动 `CompiledGraph`：遍历编译段，调用每个节点的 `ReceiveAsync`，并把返回值写入会话供下一节点使用。图决定形状；引擎决定路径、载荷与收尾方式。

- [运行时引擎](00_运行时引擎/index.md) — `RuntimeEngine`、`RunOutcome`、数据流契约与 `IGroupData`。
- [运行时会话](01_运行时会话/index.md) — `IRuntimeContext` 与 `RuntimeContext`，以及可选能力。
- [韧性契约](02_韧性契约/index.md) — 重定向、重试、暂停门、观察者、错误接收与补偿。
- [检查点与日志](03_检查点与日志/index.md) — `ExecutionCheckpoint`、`IExecutionCheckpointStore` 与日志写入契约。

```csharp
var session = new RuntimeContext { Data = "seed" };
await new RuntimeEngine().RunAsync(graph, session, CancellationToken.None);
Console.WriteLine($"{session.Status} {session.Outcome} {session.Data}");
```

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`（程序集 `VeloxDev.Core`）。纯执行之外的能力全部可选并配置在会话上；一个都不配置时，运行行为与这些能力出现之前一致。任务式教程见[工作流运行时](../../1_快速开始/05_工作流运行时/index.md)。
