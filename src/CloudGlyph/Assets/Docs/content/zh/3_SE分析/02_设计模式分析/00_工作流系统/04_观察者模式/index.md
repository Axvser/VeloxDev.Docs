# Workflow System — 设计模式 — 观察者模式

Helper 观察 `ObservableCollection` 变化和命令生命周期事件。`TreeHelper` 从 `CollectionChanged` 处理器（`OnNodesChanged`/`OnLinksChanged`）中引发 `NodeAdded/NodeRemoved/LinkAdded/LinkRemoved`；演示 `HttpHelper<T>` 订阅 `ReceiveCommand.Started/Exited/Enqueued/Dequeued` 更新运行时计数器：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/HttpHelper.cs`，第 42-82 行

```csharp
_startedHandler = e => { Interlocked.Increment(ref _activeRuns); ... };
_exitedHandler   = e => { ... if (Interlocked.Decrement(ref _activeRuns) <= 0) StopRuntimeTicker(); };
_viewModel.ReceiveCommand.Started += _startedHandler;
_viewModel.ReceiveCommand.Exited  += _exitedHandler;
```
