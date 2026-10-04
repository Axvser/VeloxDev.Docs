# 过渡动画 — 事件参数与诊断阶段

命名空间 `VeloxDev.TransitionSystem`。`TransitionEventArgs` 是效果抛出的七个生命周期事件的载荷；`TransitionEventArgs<TStage, TValue>` 为两个**诊断**事件补上有类型的阶段与值，`WarnStage` / `ErrorStage` 则指出是哪个步骤上报的。它们都派生自 `VeloxDev.TimeLine.TimeLineEventArgs`，后者携带共享的 `Handled` / `DeltaTime` / `TotalTime` 三件套（记录在 tickable 特性的 [TimeLineEventArgs](../../../06_Tickable/02_TimeLineEventArgs/index.md)，并在 [timeline](../../04_timeline/index.md) 页面复述）。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/Events/TransitionEventArgs.cs`、`TransitionEventArgs{TStage,TValue}.cs`、`Enums/WarnStage.cs`、`Enums/ErrorStage.cs`、`TransitionDiagnostics.cs`；基类 `Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`。

### 类：`TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TransitionSystem;

public class TransitionEventArgs : TimeLineEventArgs
{
    public int Loop { get; internal set; }
    public long Cycle { get; internal set; }
}
```

| 成员 | 说明 |
|---|---|
| `Loop` | `int` —— 当前**正在跑的段**是第几趟，头一趟为 `0`。拿它与 `ITransitionEffectCore.LoopTime` 比较，即可分辨「第几次重复」。 |
| `Cycle` | `long` —— 这个目标累计跑过的趟数，跨它跑过的每一条链；每跑一趟递增一次。 |
| `Handled`、`DeltaTime`、`TotalTime` | 从 `TimeLineEventArgs` 原样继承。 |

**说明：**
- 不再 `sealed` —— 下面的泛型载荷派生自它。七个无载荷生命周期事件（`Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally`）携带的就是这个基类实例，且每趟运行**只有一个共享实例**：解释器在每次回调前把 `Loop` / `Cycle` / `DeltaTime` / `TotalTime` 盖到它上面，所以处理器不能长期持有该引用。
- `Loop` 只数当前段的趟数，链中更早的段不算在它头上；`Cycle` 是整趟运行的计数器。`Seek` 可能移动运行的计数器，所以把 `Cycle` 当作「运行中的位置」，而不是私有的滴答。
- 对过渡动画而言，`DeltaTime` 是这一帧推进了多少，`TotalTime` 是**当前段开工以来**的累计；两者都不会在趟边界重置 —— 「第几趟」由 `Loop` 回答（`TransitionDiagnosticsTests.TotalTimeAccumulatesAcrossPassesWhileLoopCountsThem`）。
- *由以下测试验证：* `TimeLineEventArgsTests`（`TransitionEventArgs_Handled_DefaultFalse`、`TransitionEventArgs_Handled_SetTrue`），`TransitionDiagnosticsTests`（`EachPassIsNumberedInLoopAndCountedInCycle`、`TotalTimeAccumulatesAcrossPassesWhileLoopCountsThem`）。

### 类：`TransitionEventArgs<TStage, TValue> : TransitionEventArgs`

```csharp
namespace VeloxDev.TransitionSystem;

public sealed class TransitionEventArgs<TStage, TValue> : TransitionEventArgs
    where TStage : struct, Enum
{
    public TStage Stage { get; init; }
    public TValue? Value { get; init; }
}
```

| 成员 | 说明 |
|---|---|
| `Stage` | `TStage` —— 指出上报此事的步骤。仅 `init`。 |
| `Value` | `TValue?` —— 该步骤产出的东西；步骤无可交出时是 `null`。仅 `init`。 |

**说明：**
- `Warn` 是 `EventHandler<TransitionEventArgs<WarnStage, string>>`，其 `Value` 是人类可读的消息；`Error` 是 `EventHandler<TransitionEventArgs<ErrorStage, Exception>>`，其 `Value` 是逃逸出来的异常。旧的字符串三元组（`Stage` / `Message` / `Exception`）已不存在。
- `TransitionDiagnostics` 每次上报构造一个实例，并先把运行的 `Loop` / `Cycle` 抄上去，因此诊断处理器看到的位置与该帧的生命周期处理器一致。在任一诊断参数上置 `Handled = true` 即请求终止这趟运行。
- *由以下测试验证：* `TransitionDiagnosticsTests`（`AThrowingUpdateEndsTheRunAndIsReported`、`AThrowingSamplerIsReportedAndStopsTheFrames`、`AnUnreadablePathIsWarnedAndTheRestStillAnimates`）。

### 枚举：`WarnStage`

哪一步**降级但没有**让运行失败。每个取值每个阶段、每个实例最多上报一次。

```csharp
public enum WarnStage
{
    Unreadable,   // 某个绑定路径无法从目标读出
    Unsampled,    // 某个绑定路径上的值没有采样器
    Dropped,      // 宿主拒绝了一帧或一次派发；动画继续跑
}
```

### 枚举：`ErrorStage`

哪一步让运行失败了。`Error` 参数的 `Value` 就是逃逸出来的异常。前五个取值是引擎自身的步骤；后六个表示**该事件的某个订阅者抛了异常**。

```csharp
public enum ErrorStage
{
    Sampling,     // 采样某个绑定属性时抛出
    Run,          // 该段自身的运行循环抛出
    Marshaling,   // 把缓动后的值编组到目标上时抛出
    Awake,        // 调度器的 awake 步骤抛出
    Prepare,      // 准备这趟运行抛出

    Start,        // Start 的某个订阅者抛出
    Update,       // Update 的某个订阅者抛出
    LateUpdate,   // LateUpdate 的某个订阅者抛出
    Completed,    // Completed 的某个订阅者抛出
    Canceled,     // Canceled 的某个订阅者抛出
    Finally,      // Finally 的某个订阅者抛出
}
```

**示例：**
```csharp
var effect = new TransitionEffect { Duration = TimeSpan.FromSeconds(1) };

effect.Warn += (_, e) => Console.WriteLine($"degraded @{e.Stage}: {e.Value}");
effect.Error += (_, e) => Console.WriteLine($"failed @{e.Stage}: {e.Value}");
```

**说明：**
- 这个阶段枚举让订阅者不必解析字符串就能区分同一事件的两类失败（也就是被移除的 `Message` / `Exception` 三元组）。
- 因为枚举本身指名了步骤，`WarnStage` 与 `ErrorStage` 不可互换：「dropped」永远是 `Warn`，「marshaling」永远是 `Error`。
- *由以下测试验证：* `TransitionDiagnosticsTests`（`AThrowingSamplerIsReportedAndStopsTheFrames` —— `ErrorStage.Sampling`；`AnUnreadablePathIsWarnedAndTheRestStillAnimates` —— `WarnStage.Unreadable`）。
