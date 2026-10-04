# `TimeLineEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
    public TimeSpan DeltaTime { get; internal set; } = TimeSpan.Zero;
    public TimeSpan TotalTime { get; internal set; } = TimeSpan.Zero;
}
```

源码：`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`。

时间线系统交给用户代码的每一种载荷的基类。它携带两样东西：`Handled` 终止开关，以及同一帧里每个订阅者共享的两个时钟读数（`DeltaTime` / `TotalTime` —— 从 `FrameEventArgs` 上移到这里，好让过渡系统的事件参数也继承它们）。它是 `abstract`，因此没有公开构造函数，也无法实例化。

它是 `FrameEventArgs` 与 `TransitionEventArgs` 的基类；后者现已移入 `VeloxDev.TransitionSystem`（见过渡动画特性的[事件参数](../../03_过渡动画/00_transitionsystem/04_过渡事件参数/index.md)）。

#### 属性：`TimeLineEventArgs.Handled`

**签名：**
`public virtual bool Handled { get; set; }`

**返回：** `bool` —— 默认 `false`。

**异常：** 无。

**示例：**
```text
// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs（第 28-36 行）
var args = new FrameEventArgs();
Assert.IsFalse(args.Handled);          // 默认 false

args = new FrameEventArgs { Handled = true };
Assert.IsTrue(args.Handled);
```

**说明：**
- 声明为 `virtual` 而非 abstract —— 派生载荷可以重写这两个访问器；`FrameEventArgs` 与 `TransitionEventArgs` 都原样继承它。眼下框架里没有任何类型重写它，因此钩子收到的每种事件参数上，`Handled` 的行为都与普通字段一样。
- 源码注释里的语义是：*「False : default | True : kill the time line」*。在帧循环里，这次「kill」的作用域是当前帧阶段，而不是整个通道 —— 见快速开始的 `05_帧事件与线程安全`。
- 它是一整族里唯一**可写**的成员：用户代码写 `Handled`，其余一律只读。

#### 属性：`TimeLineEventArgs.DeltaTime`

**签名：**
`public TimeSpan DeltaTime { get; internal set; }`

**返回：** `TimeSpan` —— 距上一帧过去了多久。默认 `TimeSpan.Zero`。

**说明：**
- `internal` setter：帧泵负责写入（`TickManager` 的 `CreateFrameEventArgs`），过渡解释器每个采样写一次。用户代码只读。
- 对 tickable 特性，它是同一帧泵的帧间隔，且已套用通道的时间缩放。对过渡系统，它是这一帧推进了多少（见[过渡事件参数](../../03_过渡动画/00_transitionsystem/04_过渡事件参数/index.md)）。

#### 属性：`TimeLineEventArgs.TotalTime`

**签名：**
`public TimeSpan TotalTime { get; internal set; }`

**返回：** `TimeSpan` —— 自这条线的时间钟启动以来有多久，由时钟发布而非累加得出。默认 `TimeSpan.Zero`。

**说明：**
- `internal` setter，与 `DeltaTime` 相同。
- 对 tickable 特性，它是自通道启动以来的虚拟时间（`StopAsync` 会把它清零）。对过渡系统，它是当前段开工以来的累计 —— **不**随趟重置；「第几趟」由 `TransitionEventArgs.Loop` 回答。
- 两个读数在重定位时都**不**单调：改变步长或重启都会重新锚定时钟。
