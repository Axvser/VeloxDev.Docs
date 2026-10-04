# `FrameEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public class FrameEventArgs : TimeLineEventArgs
```

源码：`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`。

每个 `Update`、`LateUpdate` 与 `FixedUpdate` 钩子收到的东西。从 `TimeLineEventArgs` 继承 `Handled`。

**下面四个时间属性的 setter 全都是 `internal`。** 这是本类型最要紧的事实：用户代码读测量值，只写 `Handled`。这些 setter 由 `LoopChannel.CreateFrameEventArgs`（`TickManager.cs` 第 824-833 行）调用，它从一次 `TimeSample` 填充一个池化实例。

#### 属性：`FrameEventArgs.DeltaTime`

**签名：**
`public TimeSpan DeltaTime { get; internal set; }`

**返回：** `TimeSpan` —— 距**同一泵**上一帧的时间，已计入通道的时间速率。默认 `TimeSpan.Zero`。

**说明：**
- 取自时钟的采样，而不是循环自己差分计算，所以停摆的通道在这里贡献的是零，而不是一大坨（`CreateFrameEventArgs` 的备注，第 818-822 行）。
- Update 与 FixedUpdate 各有各的测量：`FixedUpdate` 里的 `DeltaTime` 是固定步长（`_fixedSampler.Step`，默认 16 ms），不是帧间隔。
- 由于采样发生在钩子运行*之前*，会阻塞的钩子改变的是**下一帧**的 `DeltaTime`，不是它自己的。
- 速率为 `0` 会让两个泵 park，因此根本不会有帧被交付 —— 也就不存在「零 delta」的帧可观察。

#### 属性：`FrameEventArgs.TotalTime`

**签名：**
`public TimeSpan TotalTime { get; internal set; }`

**返回：** `TimeSpan` —— 通道启动以来的虚拟时间，由时钟发布而不是此处累加。默认 `TimeSpan.Zero`。

**说明：**
- 不含一切停摆期，且已计入速率：它是时钟的位置，不是各次 delta 之和（`UpdatePerformanceStats`，第 906-916 行）。
- 由 `StopAsync` 重置为零。一次 `FixedUpdate` 推送收到的是 `sample.Step × stepTicks` —— 步序号乘步长 —— 而不是把最后一次读数重复（`FixedUpdateLoop`，第 480-487 行）。
- 改步长时它**不**单调：采样器重置会丢弃累加器但保留已交付的步数，于是 `TotalTime` 跳变而步序号不跳。WPF 演示因此读的是步序号而不是 `TotalTime`（`SimState.cs` 注释）。

#### 属性：`FrameEventArgs.CurrentFPS`

**签名：**
`public int CurrentFPS { get; internal set; }`

**返回：** `int` —— 实测帧率，默认 `0`。

**说明：**
- 按**墙钟**测量，不是虚拟时钟，所以时间速率减半不会让这个数字减半（`UpdatePerformanceStats` 备注，第 919 行）。
- 每墙钟秒最多重新发布一次；两次发布之间读到的是上一个值。因此短时间运行可能读到 `0`，而循环明明在跑 —— 快速开始程序为此先等 1.1 秒再打印它。

#### 属性：`FrameEventArgs.TargetFPS`

**签名：**
`public int TargetFPS { get; internal set; }`

**返回：** `int` —— 通道配置的目标帧率；第一帧构造之前为 `0`。

**说明：**
- 反映的是构造该帧那一刻的通道设置，因此它比 `SetTargetFPS` 最多晚一帧 —— 请求经由配置队列在帧边界生效。
- 循环看起来不对时，要对比的就是 `CurrentFPS` 与 `TargetFPS` 这两个数；演示两个都显示。
