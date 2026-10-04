# `TransitionEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public sealed class TransitionEventArgs : TimeLineEventArgs
```

源码：`Src/Core/VeloxDev.Core/TimeLine/TransitionEventArgs.cs`。

过渡动画系统共用的失败/信号载荷。它位于 `TimeLine` 目录，且派生自 `TimeLineEventArgs`，因此在此列出 —— 它属于同一组事件参数，但**不是** tickable 特性产生的，也没有任何 `TickManager` API 提到它。

#### 属性：`TransitionEventArgs.Stage`

**签名：**
`public string? Stage { get; init; }`

**返回：** `string?` —— 是哪个回调或阶段上报了该事件。源码中记录的预期取值是 `"Update"`、`"Finally"` 与 `"Sampling"`。

**说明：**
- 仅 `init`，所以能在对象初始化器里赋值，之后不能再改。

#### 属性：`TransitionEventArgs.Message`

**签名：**
`public string? Message { get; init; }`

**返回：** `string?` —— 该事件的人类可读描述。可能为 `null`。

#### 属性：`TransitionEventArgs.Exception`

**签名：**
`public Exception? Exception { get; init; }`

**返回：** `Exception?` —— 该事件所报告的那个异常；没有异常时为 `null`，这也是非失败信号的常态。

#### 属性：`TransitionEventArgs.Handled`

**签名：**
`public virtual bool Handled { get; set; }`

**返回：** `bool` —— 从 `TimeLineEventArgs` 原样继承，默认 `false`。本类型没有重写它。

**示例：**
```text
// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs（第 11-23 行）
var args = new TransitionEventArgs();
Assert.IsFalse(args.Handled);

args = new TransitionEventArgs { Handled = true };
Assert.IsTrue(args.Handled);

// 那两个 init-only 成员用法相同：
var reported = new TransitionEventArgs { Stage = "Update", Message = "requested rate is negative" };
```

**说明：**
- `sealed`，因此无法被扩展去携带更多信息。
- 抛出它的调用点见过渡动画特性的 API 参考；tickable 特性里没有任何地方构造或消费它。
