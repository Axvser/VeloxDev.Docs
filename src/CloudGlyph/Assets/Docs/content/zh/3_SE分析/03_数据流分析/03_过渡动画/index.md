# 数据流 — 过渡动画

## (a) 正常执行流

从 `snapshot.Execute(target)` 到帧泵的完整调用链。此流程在全部六个平台适配器上一致运行。

```plantuml
@startuml
!theme plain

actor User as User
participant "StateSnapshot" as SS
participant "TransitionCore" as TC
participant "TransitionScheduler" as Sch
participant "InterpolatorCore" as IC
participant "UIThreadInspector" as UI
participant "FrameSequence" as FS
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target (UI element)" as T

User -> SS: Execute(Rec0, CanMutualTask)
activate SS

SS -> TC: (static) Execute(target, snapshot, CanMutualTask)
activate TC

TC -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch -> Sch: return shared mutual scheduler (ConditionalWeakTable)
else CanMutualTask == false
    Sch -> Sch: return one-off non-mutual scheduler
end
Sch --> TC: scheduler
deactivate Sch

TC -> Sch: Execute(interpolator, state, effect, cts)
activate Sch

Sch -> IC: Interpolate(target, state, effect, isUIAccess, inspector)
activate IC

loop every recorded property
    IC -> UI: ProtectedGetValue(target, property)  (marshalled if needed)
    UI --> IC: currentValue
    alt custom interpolator (state.Interpolators)
        IC -> IC: customInterpolator.Interpolate(current, new, count, options)
    else registry TryGetInterpolator(propertyType)
        IC -> IC: interpolator.Interpolate(current, new, count, options)
    else IInterpolable on current or new value
        IC -> IC: value.Interpolate(current, new, count, options)
    end
    IC -> IC: output.AddPropertyInterpolations(property, frames)
end

IC --> Sch: FrameSequence (per-property frame lists, count = Duration/(1000/FPS))
deactivate IC

Sch -> TI: Execute(target, frameSequence, effect, cts)
activate TI

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start event fired

loop index in 0 .. count-1
    TI -> TI: easedIndex = GetEaseIndex(effect.Ease, index, count)
    TI -> EF: InvokeUpdate(sender, args)
    TI -> FS: Update(target, easedIndex, priority)
    activate FS
    FS -> UI: ProtectedInvoke(target, setValues, priority)
    UI -> T: property.SetValue(target, frame[prop][easedIndex])
    deactivate FS
    TI -> EF: InvokeLateUpdate(sender, args)
    TI -> TI: await WaitForFrameAsync(stopwatch, frameMs, cts)
end

TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed event fired
deactivate TI
Sch --> TC: completed
deactivate Sch
TC --> SS
deactivate TC
SS --> User: return
deactivate SS
@enduml
```

## (b) 自动往返 / 循环流

当设置了 `IsAutoReverse` 或 `LoopTime` 时，解释器会把帧遍历包起来。`LoopTime = int.MaxValue` 表示无限循环。

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "FrameSequence" as FS
participant "Effect" as EF

TI -> TI: indexs = GetEaseIndex(effect.Ease, count)
TI -> TI: frameMs = Duration / count
TI -> EF: InvokeStart(sender, args)

loop loop in 0 .. effect.LoopTime (forever when int.MaxValue)
    loop index in 0 .. count-1  (forward walk)
        TI -> TI: cts/Args.Handled check
        TI -> EF: InvokeUpdate
        TI -> FS: Update(target, indexs[index], priority)
        TI -> EF: InvokeLateUpdate
        TI -> TI: await WaitForFrameAsync(frameMs)
    end
    alt effect.IsAutoReverse
        loop index in count-1 .. 0  (backward walk)
            TI -> TI: cts/Args.Handled check
            TI -> EF: InvokeUpdate
            TI -> FS: Update(target, indexs[index], priority)
            TI -> EF: InvokeLateUpdate
            TI -> TI: await WaitForFrameAsync(frameMs)
        end
    end
end

TI -> EF: InvokeCompleted(sender, args)
EF --> TI: Completed event fired
@enduml
```

## (c) 取消 / `TransitionEventArgs.Handled = true` 短路

被取消的 `cts`（来自 `Transition.Exit` 或新的互斥动画）或处理器把 `Handled` 设为 `true` 都会抛出 `OperationCanceledException`；解释器触发 `Canceled` + `Finally` 并停止。

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "TransitionEventArgs" as Args

TI -> TI: frame loop
TI -> Args: Args.Handled read
alt Args.Handled == true  (event handler short-circuit)
    TI -> TI: throw OperationCanceledException
else cts.IsCancellationRequested (Transition.Exit / new mutual)
    TI -> TI: throw OperationCanceledException
end
TI -> EF: InvokeCancled(sender, args)
EF --> TI: Canceled event fired
TI -> EF: InvokeFinally(sender, args)
EF --> TI: Finally event fired
TI -> TI: stop immediately
@enduml
```

**应用关闭路径：** 在 `InterpolatorOutputBase.SetValues` 中，若 `inspector.IsAppAlive() == false`（例如 WinUI `DispatcherQueue` 入队失败）则跳过写入；帧停止应用且不再触发更多事件。

## (d) 互斥 vs 非互斥调度器扇出

一个目标**至多**持有一个共享互斥调度器（由 `SemaphoreSlim` 串行化），但可以同时持有**多个**并发的非互斥调度器。

```plantuml
@startuml
!theme plain

participant "StateSnapshot.Execute" as EX
participant "Target" as T
participant "MutualSchedulers (CWT)" as MWT
participant "NoMutualSchedulers (CWT)" as NWT
participant "Scheduler (mutual, shared)" as SA
participant "Scheduler (non-mutual #1)" as SB1
participant "Scheduler (non-mutual #2)" as SB2

EX -> MWT: CanMutualTask: true -> FindOrCreate(target)
MWT --> EX: shared scheduler (1 per target)
EX -> SA: Execute(interpolator, state, effect, cts)
SA -> SA: gate.WaitAsync() serializes; new mutual animation Exit()s the previous
SA -> T: apply frames (UI-marshalled)

EX -> NWT: CanMutualTask: false -> AddNoMutual(target, [scheduler])
EX -> SB1: Execute(...)
EX -> SB2: Execute(...)
SB1 -> T: apply frames in parallel
SB2 -> T: apply frames in parallel
SB1 -> NWT: RemoveNoMutual(target, [SB1]) on Completed
SB2 -> NWT: RemoveNoMutual(target, [SB2]) on Completed
@enduml
```

## 流程汇总

| 场景 | 行为 |
|---|---|
| 正常执行 | 帧按属性预计算，然后在 UI 线程经 `UIThreadInspector` 应用；每帧触发 `Update`/`LateUpdate` 事件；结束时触发 `Completed` + `Finally`。 |
| `IsAutoReverse` | 正向遍历后，解释器反向遍历帧（复用同一缓动索引列表）。 |
| `LoopTime` / `int.MaxValue` | 整个正向（+ 反向）遍历重复 `LoopTime` 次，或永远。 |
| 同目标新的互斥动画 | 新运行前 `CoreExecute` 调用 `scheduler.Exit()`；先前调度器取消其当前 `cts`。 |
| `TransitionEventArgs.Handled = true` | 抛出 `OperationCanceledException` → `Canceled` + `Finally`；时间线停止。 |
| `Transition.Exit(target)` | 取消目标的互斥（可选非互斥）调度器。 |
| 后台线程启动 | `UIThreadInspector.ProtectedInvoke`/`ProtectedGetValue`/`ProtectedInterpolate` 编组到 UI 线程。 |
| 属性无插值器 | 跳过该属性（`UnreadablePath` 哨兵或未注册插值器）；其余属性照常动画。 |
| 应用关闭 | `IsAppAlive() == false` → 跳过帧写入，不再触发事件。 |

> 源码引用：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs`（帧泵、`GetEaseIndex`、`WaitForFrameAsync`）、`TransitionScheduler.cs`（`FindOrCreate`、`Execute`、门控）、`Interpolator.cs`（解析）、`InterpolatorOutputCore.cs`（`Update`/`SetValues`、取消跳过）、`StateSnapshot.cs`（`CoreExecute`）、`Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`。
