# MonoBehaviour — API 参考

MonoBehaviour 功能在 .NET 侧提供一套类似 Unity 的帧驱动行为循环。用 `[MonoBehaviour]` 标记 `partial` 类后，Roslyn 源生成器（`VeloxDev.Core.Generator`）会让该类实现 `IMonoBehaviour`；静态 `MonoBehaviourManager` 随即驱动每个通道的 Update / LateUpdate / FixedUpdate 循环，并把每一帧转发给行为中 `partial void` 钩子。

## 命名空间

涉及两个命名空间；全部随 `VeloxDev.Core` 包分发。

| 命名空间 | 承载的公开 API |
|---|---|
| `VeloxDev.TimeLine` | `MonoBehaviourAttribute`、`MonoBehaviourManager`、`MonoBehaviourChannelEventArgs`、`TimeLineEventArgs`、`FrameEventArgs`、`ThreadSafeFrameEventArgs`、`TransitionEventArgs` |
| `VeloxDev.MonoBehaviour` | `IMonoBehaviour` |

## 模型

```csharp
// 用户 partial 类：源生成器生成 IMonoBehaviour 的实现。
[MonoBehaviour]
public partial class Behaviour
{
    public Behaviour() => InitializeMonoBehaviour();

    partial void Awake();
    partial void Start();
    partial void Update(FrameEventArgs e);
    partial void LateUpdate(FrameEventArgs e);
    partial void FixedUpdate(FrameEventArgs e);
}
```

- `[MonoBehaviour]` 选定循环通道，并可选指定注册时的目标帧率。
- `InitializeMonoBehaviour()`（由生成器生成）负责注册实例；`CloseMonoBehaviour()`（由生成器生成）负责注销。
- `MonoBehaviourManager` 拥有各通道的循环；生命周期与配置均为线程安全操作，在帧边界生效。
- 行为将 `FrameEventArgs.Handled = true` 置位后，会跳过该帧阶段其余行为。
- 各通道的 `OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` 事件上报生命周期迁移。

证据来源：源码（`Src/Core/VeloxDev.Core/TimeLine/`、`Src/Core/VeloxDev.Core/Interfaces/MonoBehaviour/`）、源生成器（`Src/Generators/VeloxDev.Core.Generator/`）、WPF 示例（`Examples/MonoBehaviour/WPF/Demo/`）与 MSTest 测试套件（`Src/Core/VeloxDev.Core.Test/TimeLine/`）。

## 按类型浏览 API

本功能的 API 参考按类型拆分，每个页面完整记录一个类型的公开表面。

| 类型 | 命名空间 | 种类 | 页面 |
|---|---|---|---|
| `MonoBehaviourAttribute` | `VeloxDev.TimeLine` | 类特性 | [MonoBehaviourAttribute](00_MonoBehaviourAttribute/index.md) |
| `MonoBehaviourManager` | `VeloxDev.TimeLine` | 静态管理器 | [MonoBehaviourManager](01_MonoBehaviourManager/index.md) |
| `TimeLineEventArgs` | `VeloxDev.TimeLine` | 抽象基类 | [TimeLineEventArgs](02_TimeLineEventArgs/index.md) |
| `FrameEventArgs` | `VeloxDev.TimeLine` | 类 | [FrameEventArgs](03_FrameEventArgs/index.md) |
| `ThreadSafeFrameEventArgs` | `VeloxDev.TimeLine` | 类 | [ThreadSafeFrameEventArgs](04_ThreadSafeFrameEventArgs/index.md) |
| `MonoBehaviourChannelEventArgs` | `VeloxDev.TimeLine` | 类 | [MonoBehaviourChannelEventArgs](05_MonoBehaviourChannelEventArgs/index.md) |
| `TransitionEventArgs` | `VeloxDev.TimeLine` | 类 | [TransitionEventArgs](06_TransitionEventArgs/index.md) |
| `IMonoBehaviour` | `VeloxDev.MonoBehaviour` | 接口 | [IMonoBehaviour](07_IMonoBehaviour/index.md) |
