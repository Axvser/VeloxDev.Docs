# Workflow System — Design Patterns — Observer Pattern

Helpers observe `ObservableCollection` changes and command lifecycle events. `TreeHelper` raises `NodeAdded/NodeRemoved/LinkAdded/LinkRemoved` from `CollectionChanged` handlers (`OnNodesChanged`/`OnLinksChanged`); the demo `HttpHelper<T>` subscribes `ReceiveCommand.Started/Exited/Enqueued/Dequeued` to update runtime counters:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/HttpHelper.cs`, lines 42-82

```csharp
_startedHandler = e => { Interlocked.Increment(ref _activeRuns); ... };
_exitedHandler   = e => { ... if (Interlocked.Decrement(ref _activeRuns) <= 0) StopRuntimeTicker(); };
_viewModel.ReceiveCommand.Started += _startedHandler;
_viewModel.ReceiveCommand.Exited  += _exitedHandler;
```
