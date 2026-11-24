# 调度与事件

调度器拥有循环；解释器产出帧；宿主提供线程归属与存活状态。运行时类命名空间为 `VeloxDev.TransitionSystem.Abstractions`；调度器、宿主、解释器三个接口在 `VeloxDev.TransitionSystem`。

## VeloxDev.TransitionSystem

### 接口：ITransitionSchedulerCore

**签名：** `public interface ITransitionSchedulerCore`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Execute` | `Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | 让 `producer` 针对 `state` 运行。 |
| `Exit` | `void Exit()` | 停止调度器。 |

### 接口：ITransitionScheduler

`ITransitionSchedulerCore` 的空精化，用于优先级类型被擦除之处。

**签名：** `public interface ITransitionScheduler : ITransitionSchedulerCore`

### 接口：ITransitionScheduler<TPriorityCore>

**签名：** `public interface ITransitionScheduler<TPriorityCore> : ITransitionSchedulerCore`

| 成员 | 签名 |
|---|---|
| `Execute` | `Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` |

### 接口：ITransitionHost<TPriorityCore>

`IThreadDispatcher<TPriorityCore>` 与 `IApplicationState` 的组合；本身不增加成员。

**签名：** `public interface ITransitionHost<TPriorityCore> : IThreadDispatcher<TPriorityCore>, IApplicationState`

### 接口：ITransitionInterpreter<TPriorityCore>

**签名：** `public interface ITransitionInterpreter<TPriorityCore> : IDisposable`

| 成员 | 类型/签名 | 说明 |
|---|---|---|
| `Args` | `TransitionEventArgs { get; set; }` | 当前执行的参数。 |
| `Execute` | `Task Execute(object target, SamplerSet<TPriorityCore> samplerSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts)` | 逐帧执行一个过渡。 |
| `Exit` | `void Exit()` | 停止解释器。 |

## VeloxDev.TransitionSystem.Abstractions

### 类：FramePacerCore

决定采样循环下一帧何时发生。默认在线程池定时器上等待；拥有 UI 线程的宿主覆盖 `Arm` / `Disarm` 以在该线程等待，续体因此在那里恢复，属性写入无需派发。

**签名：** `public abstract class FramePacerCore : IDisposable`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Schedule` | `void Schedule(Action continuation, TimeSpan interval, CancellationToken cancellationToken)` | 在 `interval` 之后（不早于）运行一次 `continuation`；令牌已取消时立即运行。挂起的续体会被替换而非排队。 |
| `Arm` | `protected abstract void Arm(TimeSpan interval)` | 启动或重新武装等待。每帧调用一次。 |
| `Disarm` | `protected abstract void Disarm()` | 结束等待；必须容忍未武装状态且不得分配。 |
| `Fire` | `protected void Fire()` | 恰好调用一次挂起的续体。在等待完成时调用。 |
| `Dispose` | `virtual void Dispose()` | 结束等待并释放挂起的续体。 |

默认节拍器由解释器提供；适配器覆盖节拍器工厂以把循环绑定到自己的 UI 线程。

### 类：TransitionSchedulerCore

非泛型调度器。

**签名：** `public abstract class TransitionSchedulerCore : ITransitionSchedulerCore`

| 成员 | 签名 | 说明 |
|---|---|---|
| `MutualSchedulers` | `static ConditionalWeakTable<object, ITransitionSchedulerCore> { get; protected set; }` | 每个目标的互斥调度器。 |
| `NoMutualSchedulers` | `static ConditionalWeakTable<object, ConcurrentDictionary<ITransitionSchedulerCore, byte>> { get; }` | 每个目标的并发调度器（setter 为 internal）。 |
| `TryGetMutualScheduler` | `static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler)` | 查找互斥调度器。 |
| `TryGetNoMutualScheduler` | `static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers)` | 查找并发调度器。 |
| `RemoveNoMutualScheduler` | `static bool RemoveNoMutualScheduler(object source)` | 移除并发调度器集合。 |
| `TargetRef` | `virtual WeakReference<object>? TargetRef { get; }` | 弱持有的目标。 |
| `Execute` | `abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | 运行一趟。 |
| `Exit` | `abstract void Exit()` | 停止调度器。 |

### 类：TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>

**签名：**
`public class TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore> : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore> where THost : ITransitionHost<TPriorityCore>, new() where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Execute` | `override Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | 擦除入口；效果不是该优先级的强类型时立即返回。 |
| `Execute` | `virtual Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` | 强类型一趟。 |
| `ExecuteCapturing` | `virtual Task<SamplerSet<TPriorityCore>?> ExecuteCapturing(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` | 运行一段并返回已准备的帧集以便重放。 |
| `Replay` | `virtual Task Replay(SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` | 用相同端点重跑同一段，不重读目标、不重发 `Awake`。 |
| `Exit` | `override void Exit()` | 停止调度器。 |
| `FindOrCreate<T>` | `static ITransitionScheduler<TPriorityCore> FindOrCreate<T>(T source, bool CanMutualTask = true) where T : class` | 取出登记在 `source` 下的调度器；这是唯一会登记它的路径，后续控制调用才能找到该动画。 |

受保护静态字段 `host` 持有 `THost` 实例。

### 类：TransitionInterpreterCore

**签名：** `public abstract class TransitionInterpreterCore : IDisposable`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Args` | `virtual TransitionEventArgs Args { get; set; }` | 传给每个效果回调的参数。 |
| `Exit` | `virtual void Exit()` | 停止采样循环。 |
| `Dispose` | `virtual void Dispose()` | 释放运行资源。 |

受保护状态含 `cts`。派生类型通过受保护面覆盖帧节拍器创建，以提供宿主自己的节拍器。

### 类：TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore>

**签名：** `public abstract class TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore> where TTransitionEffectCore : ITransitionEffect<TPriorityCore>`

| 成员 | 签名 |
|---|---|
| `Execute` | `virtual Task Execute(object target, SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts)` |

### 类：TransitionInterpreterCore<TTransitionEffectCore>

不使用调度优先级的宿主版本。

**签名：** `public abstract class TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter<NonPriority> where TTransitionEffectCore : ITransitionEffectCore`

| 成员 | 签名 |
|---|---|
| `Execute` | `virtual Task Execute(object target, SamplerSet<NonPriority> frameSet, ITransitionEffect<NonPriority> effect, CancellationTokenSource cts)` |

### 类：TransitionHostBase<TPriorityCore>

**签名：** `public abstract class TransitionHostBase<TPriorityCore> : ThreadDispatcherBase<TPriorityCore>, ITransitionHost<TPriorityCore>`

| 成员 | 类型 | 说明 |
|---|---|---|
| `IsAlive` | `virtual bool IsAlive { get; }` | 生命周期是否仍存活；不存活时采样循环停止。 |

继承的 `IThreadDispatcher<TPriorityCore>` 成员（`ThreadFor`、`Post` 等）负责把工作送到目标线程。

## 事件

效果回调收到 `TransitionEventArgs` 或 `TransitionEventArgs<TStage, TValue>`；这两个类型及 `ErrorStage` / `WarnStage` 枚举见[效果与缓动](../01_效果与缓动/index.md)。

## 示例

```csharp
using System.Windows.Threading;
using VeloxDev.TransitionSystem;

// 适配器提供这一对；WPF 包已经提供。
var scheduler = TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>
    .FindOrCreate(box);
```

应用代码通常只通过 `Transition<T>.Execute`、`ThemeManager.Transition` 或 `InterpolatorCore.CreateScheduler` 触及调度器。见[平台适配类型](../04_平台适配类型/index.md)。
