# 数据流 — 过渡动画系统

## 执行状态快照（`snapshot.Execute(target)`）

从 `Execute` 到帧泵的完整调用链。此流程在全部六个平台适配器上一致运行。

```plantuml
@startuml
!theme plain

actor User as User
participant "StateSnapshot" as SS
participant "TransitionCore" as TC
participant "TransitionScheduler" as Sch
participant "Interpolator" as IC
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
    Sch -> Sch: 返回共享调度器 (ConditionalWeakTable)
else false
    Sch -> Sch: 返回一次性非互斥调度器
end
Sch --> TC: scheduler
deactivate Sch

TC -> Sch: Execute(interpolator, state, effect, cts)
activate Sch

Sch -> IC: Interpolate(target, state, effect, isUIAccess, inspector)
activate IC

loop 每个记录的属性
    IC -> IC: TryGetInterpolator(propertyType) -> IValueInterpolator
    IC -> IC: 起始/结束值上的 IInterpolable? 回退
    IC -> IC: 构建 List<object?> 帧 (steps = Duration/(1000/FPS))
end

IC --> Sch: FrameSequence（每属性帧列表）
deactivate IC

Sch -> TI: Execute(target, frameSequence, effect, isUIAccess, cts)
activate TI

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start 事件已触发

loop index in 0 .. frames.Count-1
    TI -> TI: easedIndex = GetEaseIndex(effect.Ease, index, count)
    TI -> FS: Update(target, easedIndex, isUIAccess, priority)
    activate FS
    loop 每个属性
        FS -> UI: IsUIThread()?
        alt 在 UI 线程
            FS -> T: property.SetValue(target, frame[prop][easedIndex])
        else 不在 UI 线程
            UI -> UI: ProtectedInvoke(false, action)（调度到 UI 线程）
            UI -> T: property.SetValue(target, frame[prop][easedIndex])
        end
    end
    deactivate FS
    TI -> EF: InvokeUpdate(sender, args)
    TI -> TI: await Delay(duration/count)
end

alt IsAutoReverse
    TI -> TI: 反向遍历帧（反转索引）
end

alt LoopTime > 1 或 int.MaxValue
    TI -> TI: 重复循环（LoopTime 次，或永远）
end

TI -> EF: InvokeCompleted(sender, args)
deactivate TI
Sch --> TC: 完成
deactivate Sch
TC --> SS
deactivate TC
SS --> User: 返回
deactivate SS
@enduml
```

## 取消与异常路径

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "TransitionEventArgs" as Args

TI -> TI: 帧循环
TI -> TI: Args.Handled == true?
alt Handled == true
    TI -> EF: InvokeCancled(sender, args)
    TI -> EF: InvokeFinally(sender, args)
    TI -> TI: 立即停止
else 通过 CTS 取消 (Transition.Exit)
    TI -> EF: InvokeCancled(sender, args)
    TI -> EF: InvokeFinally(sender, args)
    TI -> TI: 立即停止
else 应用关闭 (IsAppAlive() == false)
    TI -> TI: 停止且不再触发调用
end
@enduml
```

## 正常 / 异常路径总结

| 场景 | 行为 |
|---|---|
| 正常执行 | 帧在 UI 线程经 `UIThreadInspector` 应用；每帧触发 `Update`/`LateUpdate` 事件；结束时触发 `Completed` + `Finally`。 |
| 同目标新的互斥动画 | 新动画运行前，先前调度器被 `Exit()`（当前动画被取消）。 |
| `TransitionEventArgs.Handled = true` | 短路时间线；触发 `Canceled` + `Finally` 事件。 |
| `Transition.Exit(target)` | 取消目标的互斥（可选非互斥）调度器。 |
| 后台线程启动 | `UIThreadInspector.ProtectedInvoke(false, action)` 把帧写调度回 UI 线程。 |
| 属性无插值器 | 跳过该属性；其余属性照常动画。 |

> 源码引用：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs`（帧泵）、`TransitionScheduler.cs`（`FindOrCreate`、`Execute`）、`Interpolator.cs`（解析）、`InterpolatorOutputCore.cs`（`Update`）、`Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`。
