# Transition — 命名空间：`VeloxDev.TimeLine`

### 类：`TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;
public sealed class TransitionEventArgs : TimeLineEventArgs { }
```

空类型；继承自 `TimeLineEventArgs` 的 `bool Handled { get; set; }`。在效果事件处理器内把 `Handled` 设为 `true` 会短路动画时间线（解释器抛出 `OperationCanceledException`，触发 `Canceled` + `Finally`）。
**验证依据：** `TransitionEffectCoreTests`（`Events_AreInvoked`）。
