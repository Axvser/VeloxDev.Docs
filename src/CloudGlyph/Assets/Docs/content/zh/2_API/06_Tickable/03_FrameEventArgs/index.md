# `FrameEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public class FrameEventArgs : TimeLineEventArgs
{
    public int CurrentFPS { get; internal set; } = 0;
    public int TargetFPS { get; internal set; } = 0;
}
```

源码：`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`。

每个 `Update`、`LateUpdate`、`FixedUpdate` 钩子收到的载荷。它只声明两个帧率读数；`Handled`、`DeltaTime` 与 `TotalTime` 继承自 [TimeLineEventArgs](../02_TimeLineEventArgs/index.md)（时钟读数上移到基类，好让过渡系统的事件参数共享它们）。

**这一族的每个属性都是 `internal` setter** —— 用户代码读测量值，只写 `Handled`。setter 由 `LoopChannel.CreateFrameEventArgs` 调用（`TickManager.cs` 第 824-833 行），它用一次 `TimeSample` 填充一个池化实例。

#### 属性：`FrameEventArgs.CurrentFPS`

**签名：**
`public int CurrentFPS { get; internal set; }`

**返回：** `int` —— 实测每秒帧数，默认 `0`。

**说明：**
- 按**墙钟**测量，而不是虚拟时钟，所以把时间缩放减半不会让这个数字减半（`UpdatePerformanceStats` 备注，第 919 行）。
- 每个墙钟秒最多重新发布一次；两次发布之间读到的还是旧值。因此短时间运行可能在这里读到 `0`，而循环明明在跑 —— 快速开始的程序因此先等 1.1 秒再打印它。

#### 属性：`FrameEventArgs.TargetFPS`

**签名：**
`public int TargetFPS { get; internal set; }`

**返回：** `int` —— 通道配置的目标值；第一帧构建之前为 `0`。

**说明：**
- 反映构建该帧那一刻的通道设置，所以落后 `SetTargetFPS` 至多一帧 —— 请求经配置队列、在帧边界才应用。
- 当循环看起来不对时，要对比的就是 `CurrentFPS` 与 `TargetFPS` 这两个数；演示把两者都显示出来。

#### 继承：`DeltaTime`、`TotalTime`、`Handled`

三者都原样来自 `TimeLineEventArgs`（源：`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`）；本类型没有重写它们。

- `DeltaTime`（`TimeSpan`，`internal` set）—— 距**同一个泵**上一帧过去了多久，已套用通道的时间缩放。取自时钟采样，而不是循环自行求差，所以卡住的通道在这里不会一次性补一大块，而是什么都不贡献（`CreateFrameEventArgs` 备注，第 818-822 行）。Update 与 FixedUpdate 各有各的测量：`FixedUpdate` 里的 `DeltaTime` 是固定步长（`_fixedSampler.Step`，默认 16 ms），不是帧间隔。因为采样发生在钩子运行**之前**，阻塞的钩子影响的是**下一帧**的 `DeltaTime`，而不是它自己的。
- `TotalTime`（`TimeSpan`，`internal` set）—— 自通道启动以来的虚拟时间，由时钟发布而非累加得出。它排除一切停顿所耗，且套用了速率，`StopAsync` 会把它清零。`FixedUpdate` 推入的是 `sample.Step × stepTicks` —— 步序号乘以步长。改变步长时它**不**单调：重定基会丢弃累加器并保留已投递步数，于是 `TotalTime` 跳变，而步序号不跳。
- `Handled`（`bool`，`get; set;`）—— 唯一可写的成员。构建帧时为 `false`；钩子置 `true` 可停止该帧阶段余下的行为。
