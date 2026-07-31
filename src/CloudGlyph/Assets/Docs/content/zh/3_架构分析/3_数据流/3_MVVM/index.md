# 数据流 — MVVM

## （a）设置 `[VeloxProperty]` 字段

生成的 setter（默认模式）触发变更通知并转发到 partial 钩子。setter 行来源：`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`，`GetSetterBodyLines`，第 287-307 行。

```plantuml
@startuml
!theme plain

participant "用户代码" as User
participant "生成的 setter (Index)" as Setter
participant "ObservableViewModelBase" as Base
participant "partial 钩子 (OnIndexChanged)" as Hook
participant "Binding (TextBlock)" as Binding

User -> Setter: Index = 1
activate Setter
Setter -> Setter: Object.Equals(_index, value)? 相等则返回
Setter -> Base: OnPropertyChanging(nameof(Index))
activate Base
Base --> Setter
deactivate Base
Setter -> Hook: OnIndexChanging(old, new)
Setter -> Setter: _index = value
Setter -> Hook: OnIndexChanged(old, new)
activate Hook
Hook -> Hook: MinusCommand.Notify()
Hook --> Setter
deactivate Hook
Setter -> Base: OnPropertyChanged(nameof(Index))
activate Base
Base -> Binding: PropertyChanged(this, args)
Binding -> Binding: 读取 Index，更新 TextBlock
Base --> Setter
deactivate Base
Setter --> User
deactivate Setter
@enduml
```

## （b）执行 `[VeloxCommand]`

经过 `ExecuteAsync` → 信号量 / 队列 → 生命周期事件的流程（VeloxCommand.cs，第 139-174、176-204、206-222 行）。

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "IVeloxCommand" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "_pendingQueue" as Queue
participant "用户方法 (Plus)" as Method

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: new CommandEventArgs(Created) + 触发 Created
Cmd -> Lock: _stateLock.WaitAsync()
activate Lock
alt _isForceLocked == true
    Cmd -> Cmd: item.Cts?.Cancel() + 触发 Canceled
else _active.Count < _maxConcurrency
    Cmd -> Cmd: _active.Add(item)
    Lock --> Cmd
    deactivate Lock
    Cmd -> Cmd: 触发 Started
    Cmd -> Method: await _command(parameter, ct)
    activate Method
    Method --> Cmd: 返回 / 抛出
    deactivate Method
    alt 成功
        Cmd -> Cmd: 触发 Completed
    else OperationCanceledException
        Cmd -> Cmd: 触发 Canceled
    else Exception
        Cmd -> Cmd: 触发 Failed (带 ex)
    end
    Cmd -> Cmd: _active.Remove(item) + 触发 Exited
    Cmd -> Cmd: RaiseCanExecuteChanged()
    Cmd -> Cmd: TryStartPendingAsync()
else 排队（信号量耗尽）
    Cmd -> Queue: _pendingQueue.Enqueue(item)
    Cmd -> Cmd: 触发 Enqueued
    Queue --> Cmd
end
Lock --> Cmd
deactivate Lock
Cmd --> UI
deactivate Cmd
@enduml
```

## （c）`Notify()` 触发的 CanExecute 流程

```plantuml
@startuml
!theme plain

participant "Index setter" as Setter
participant "partial OnIndexChanged" as Hook
participant "MinusCommand" as Cmd
participant "WPF 绑定引擎" as WPF

Setter -> Hook: OnIndexChanged(old, new)
Hook -> Cmd: MinusCommand.Notify()
Cmd -> Cmd: RaiseCanExecuteChanged()
Cmd --> WPF: CanExecuteChanged 事件
WPF -> Cmd: CanExecute(null)
Cmd -> Cmd: (_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked
Note right of Cmd: 委托给 CanExecuteMinusCommand -> _index > 0
WPF -> WPF: 启用 / 禁用绑定的 Button
@enduml
```

## 错误 / 并发路径总结

| 场景 | 行为 |
|---|---|
| 强制锁定时触发（`Lock()`） | `ExecuteAsync` 取消新条目并触发 `Canceled`；不开始执行。 |
| 容量耗尽（`_active.Count == _maxConcurrency`） | 条目入队并触发 `Enqueued`；当容量释放或执行 `UnLock` / `Continue` / `ChangeSemaphore` 后，`TryStartPendingAsync` 出队（触发 `Dequeued`）。 |
| 用户方法抛出异常 | 触发 `Failed`（`CommandEventArgs.Exception`）；`Exited` 仍会触发。 |
| `OperationCanceledException` | 触发 `Canceled`。 |
| `Interrupt()` | 取消活动 CTS，随后 `UnLockAsync` 重新允许触发。 |
| `Clear()` | 取消活动并出队所有待处理项，对每个条目触发 `Dequeued` 再触发 `Canceled`。 |

> 源引用：`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`（`ExecuteAsync`、`ExecuteCoreAsync`、`OnExecutionCompletedAsync`、`TryStartPendingAsync`、`InterruptAsync`、`ClearAsync`）、`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`GetSetterBodyLines`、`GenerateCollectionMembers`）、`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。
