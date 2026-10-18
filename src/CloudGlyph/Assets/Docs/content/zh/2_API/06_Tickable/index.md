# Tickable — API 参考

tickable 特性在 .NET 侧提供一套帧驱动行为循环。用 `[Tickable]` 标记 `partial` 类后，Roslyn 源生成器（`VeloxDev.Core.Generator`）会让该类实现 `VeloxDev.TimeLine.ITickable`；静态 `TickManager` 随即驱动每个通道的 Update / LateUpdate / FixedUpdate 循环，并把每一帧转发给行为中 `partial void` 钩子。

## 命名空间

全部随 `VeloxDev.Core` 包分发。

| 命名空间 | 承载的公开 API |
|---|---|
| `VeloxDev.TimeLine` | `TickableAttribute`、`TickManager`、`TickChannelEventArgs`、`ITickable`、`TimeLineEventArgs`、`FrameEventArgs` |
| `VeloxDev.Timing` | `ITimeSource`、`ITimeSourceControl` —— 通道的时钟，经 `TickManager.Bus` 取得。属于共享基础设施，随过渡动画特性一并记录 |

## 模型

```csharp
// 用户 partial 类：源生成器生成 ITickable 的实现。
[Tickable("demo", 60)]
public partial class Behaviour
{
    public Behaviour() => InitializeTickable();      // 生成的

    partial void Awake();
    partial void Start();
    partial void Update(FrameEventArgs e);
    partial void LateUpdate(FrameEventArgs e);
    partial void FixedUpdate(FrameEventArgs e);
}
```

- `[Tickable]` 选定循环通道，并可选指定注册时的目标帧率。
- `InitializeTickable()`（由生成器生成）负责注册实例；`CloseTickable()`（由生成器生成）负责注销。
- `TickManager` 拥有各通道的循环。每个修改器都可从任意线程调用；目标帧率变更在帧边界生效，速率直接作用于总线，步长变更交给 fixed 泵。
- 行为将 `FrameEventArgs.Handled = true` 置位后，会跳过该帧阶段其余行为。
- `OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` 事件上报所有通道的生命周期迁移。

证据来源：源码（`Src/Core/VeloxDev.Core/TimeLine/`、`Src/Core/VeloxDev.Core/Interfaces/Tickable/`）、源生成器（`Src/Generators/VeloxDev.Core.Generator/Tickable.cs` 与 `Writers/TickWriter.cs`）、WPF 示例（`Examples/Tickable/WPF/Demo/`）与 MSTest 测试套件（`Src/Core/VeloxDev.Core.Test/TimeLine/`）。

## 按类型浏览公开表面

| 类型 | 种类 | 公开成员 | 页面 |
|---|---|---|---|
| `TickableAttribute` | sealed class : `Attribute` | 2 属性、1 构造函数 | [TickableAttribute](00_TickableAttribute/index.md) |
| `TickManager` | 静态类 | 4 事件、3 个属性/常量（`DEFAULT_CHANNEL`、`UseAsyncLoop`、`ChannelNames`）、27 个静态方法 —— 合计 34 个公开成员 | [TickManager](01_TickManager/index.md) |
| `TimeLineEventArgs` | 抽象类 | 3 属性 | [TimeLineEventArgs](02_TimeLineEventArgs/index.md) |
| `FrameEventArgs` | class : `TimeLineEventArgs` | 2 个只读属性（internal set）+ 3 个继承 | [FrameEventArgs](03_FrameEventArgs/index.md) |
| `TickChannelEventArgs` | sealed class : `EventArgs` | 1 属性 | [TickChannelEventArgs](04_TickChannelEventArgs/index.md) |
| `ITickable` | 接口 | 7 个方法 | [ITickable](05_ITickable/index.md) |

`TransitionEventArgs` **不属于本特性**：它位于 `VeloxDev.TransitionSystem`，随过渡动画特性记录。

以下内容**不属于**公开表面，也不应出现在用户代码里 —— 它们是 `TickManager` 内部的 `private`：嵌套类型 `LoopChannel`、`BehaviorWrapper`、`ConfigChangeRequest`、`ObjectPool<T>`，以及 `GetOrCreateChannel`、所有返回 `LoopChannel` 的方法和各泵方法。公开途径只有静态门面与 `TickManager.Bus`。

## `TickManager` 的类型级索引

`TickManager` 是一个拥有 34 个公开成员的门面，因此它的参考文档按成员分组拆分：

| 分组 | 成员 |
|---|---|
| 生命周期与注册 | `Start`、`StopAsync`、`Pause`、`Resume`、`TogglePause`、`RestartAsync`、`RegisterBehaviour`、`UnregisterBehaviour` |
| 配置 | `UseAsyncLoop`、`SetTargetFPS`、`SetFixedUpdateInterval`、`SetTimeScale`、`ExecuteOnMainThread`、`SetUseAsyncLoop`、`ClearUseAsyncLoopOverride`、`DEFAULT_CHANNEL`、`ChannelNames` |
| 状态查询 | `IsRunning`、`IsPaused`、`CurrentFPS`、`TargetFPS`、`TotalTime`、`TotalTimeMs`、`TotalFrames`、`ActiveBehaviorCount`、`TimeScale`、`SystemStatus`、`IsUpdateThreadAlive`、`IsFixedUpdateThreadAlive`、`Bus` |
| 事件 | `OnChannelStarted`、`OnChannelPaused`、`OnChannelResumed`、`OnChannelStopped` |
