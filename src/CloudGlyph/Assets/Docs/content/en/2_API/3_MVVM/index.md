# MVVM — API Reference

## Namespace: `VeloxDev.MVVM`

### VeloxCommand

| Constructor | Description |
|---|---|
| `VeloxCommand(Func<Task>)` | Async command with no parameter |
| `VeloxCommand(Action<object?>)` | Sync command with parameter |
| `VeloxCommand(Func<object?, Task>)` | Async command with parameter |
| `VeloxCommand(Func<object?, CancellationToken, Task>)` | Full async with cancellation token |
| `VeloxCommand(Func<object?, CancellationToken, Task>, Predicate<object?>, int)` | Full with canExecute + semaphore |

| Method | Description |
|---|---|
| `Execute(object?)` | Execute the command |
| `CanExecute(object?)` | Check if executable |
| `Lock() / Unlock()` | Manual semaphore control |
| `Interrupt() / Continue()` | Pause/resume execution |
| `ChangeSemaphore(int)` | Change concurrency limit |
| `Notify()` | Refresh CanExecute state |

| Event | Description |
|---|---|
| `Created` | Command was created |
| `Started` | Execution started |
| `Completed` | Execution succeeded |
| `Failed` | Execution failed |
| `Canceled` | Execution canceled |
| `Exited` | Lifecycle ended (called after Started/Completed/Failed) |
| `Enqueued` | Command queued (semaphore busy) |
| `Dequeued` | Command dequeued (semaphore available) |

### Attributes (Source Generator)

| Attribute | Target | Description |
|---|---|---|
| `[VeloxProperty]` | Field | Generates observable property with INotifyPropertyChanged |
| `[VeloxCommand]` | Method | Generates command property from method |
