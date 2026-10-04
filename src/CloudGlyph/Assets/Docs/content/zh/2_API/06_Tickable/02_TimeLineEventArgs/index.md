# `TimeLineEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public abstract class TimeLineEventArgs
```

源码：`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`。

时间线系统交给用户代码的每一种载荷的基类。它存在的理由只有一个：把 `Handled` 带给全部三种事件参数类型，而不必各处重复。它是 `abstract`，因此没有公开构造函数，也无法实例化。

它是 `FrameEventArgs`（因而也是 `ThreadSafeFrameEventArgs`）与 `TransitionEventArgs` 的基类。

#### 属性：`TimeLineEventArgs.Handled`

**签名：**
`public virtual bool Handled { get; set; }`

**返回：** `bool` —— 默认 `false`。**异常：** 无。

**示例：**
```text
// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs（第 13-22 行）
var args = new TransitionEventArgs();
Assert.IsFalse(args.Handled);          // 默认 false

args = new TransitionEventArgs { Handled = true };
Assert.IsTrue(args.Handled);
```

**说明：**
- 声明为 `virtual` 而非 abstract —— 派生载荷可以重写这两个访问器（`ThreadSafeFrameEventArgs` 用的是 `new` 而不是 `override`，那是另一回事，也是个陷阱；见 `04_ThreadSafeFrameEventArgs`）。
- 源码注释里的语义是：*「False : default | True : kill the time line」*。在帧循环里，这次「kill」的作用域是当前帧阶段，而不是整个通道 —— 见快速开始的 `05_帧事件与线程安全`。
- 它是 `FrameEventArgs` 上唯一可写的成员；四个时间属性都是 `internal` setter。
