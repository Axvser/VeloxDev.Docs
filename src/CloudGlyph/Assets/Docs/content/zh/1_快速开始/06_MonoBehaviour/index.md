# MonoBehaviour — 快速开始

**monobehaviour** 特性把 Unity 风格的行为循环带到纯 .NET。你给一个 `partial` 类打上 `[MonoBehaviour]`，Roslyn 源生成器（位于程序集 `VeloxDev.Core.Generator`）就把桥接写进 `.g.cs`：该类实现运行时接口 `VeloxDev.MonoBehaviour.IMonoBehaviour`，并获得生命周期入口 `Awake`、`Start`、`Update`、`LateUpdate`、`FixedUpdate` 作为 `partial void` 钩子，由你在类的另一半自行实现。不需要继承基类、没有可重写的虚方法 `OnFrame`、也没有 `[Update]` 特性 —— 钩子方法本身就是 API。

运行时方面，静态门面 `VeloxDev.TimeLine.MonoBehaviourManager` 驱动多个具名**通道（channel）**。每个通道拥有两个帧泵：Update 泵（按目标 FPS、默认 60 派发每帧的 `Update` / `LateUpdate`）与 FixedUpdate 泵（固定步长 `FixedUpdate`，默认每 16 ms 一次）。两个泵在后台线程上运行（当平台禁止 `Thread` —— 例如 WASM/iOS —— 则改为 `async` 任务），并按注册顺序调用该通道上每个行为的钩子。管理器还提供按通道的配置（`SetTargetFPS`、`SetFixedUpdateInterval`、`SetTimeScale`、`SetUseAsyncLoop`、`ExecuteOnMainThread`）、生命周期控制（`Start`、`StopAsync`、`Pause`、`Resume`、`TogglePause`、`RestartAsync`）与状态查询（`SystemStatus`、`IsRunning`、`CurrentFPS`、`TotalFrames`、`ActiveBehaviorCount` 等）。

关键公开类型及其位置：

- `VeloxDev.TimeLine.MonoBehaviourAttribute` —— 类特性，带 `channel` / `fps` 参数。
- `VeloxDev.TimeLine.MonoBehaviourManager` —— 静态通道运行时。
- `VeloxDev.TimeLine.FrameEventArgs`、`VeloxDev.TimeLine.TimeLineEventArgs`、`VeloxDev.TimeLine.ThreadSafeFrameEventArgs`、`VeloxDev.TimeLine.TransitionEventArgs` —— 传给钩子的事件载荷类型。
- `VeloxDev.MonoBehaviour.IMonoBehaviour` —— 生成器替你实现的接口。
- `VeloxDev.TimeLine.MonoBehaviourChannelEventArgs` —— 通道 `OnChannel*` 事件的载荷。

一切皆为纯 .NET（`VeloxDev.Core` 目标框架为 `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`）。**循环本身不需要 UI 适配器、不需要服务、不需要配置文件** —— 生成器唯一的要求是类必须 `partial`。仓库附带一个 WPF GUI 示例（`Examples/MonoBehaviour/WPF/Demo`），`Src/Core/VeloxDev.Core.Test/TimeLine/` 下的测试则无头地驱动该循环。

## 快速开始 — 子页面

本特性的快速入门拆分为下列页面（逐步导向最后一页那个可运行的单文件程序）：

- [00 前置条件](00_前置条件/) — 支持目标、SDK/运行时，以及“控制台宿主、无需服务”说明
- [01 安装依赖](01_安装依赖/) — 从 NuGet 添加 `VeloxDev.Core`，或在本仓库中项目引用它
- [02 定义行为](02_定义行为/) — `[MonoBehaviour]` 类、`channel` / `fps` 与生成的 `partial void` 生命周期钩子
- [03 运行与配置循环](03_运行与配置循环/) — 通道配置旋钮、`Start` / `StopAsync`、状态查询与通道事件
- [04 暂停恢复与重启](04_暂停恢复与重启/) — `Pause` / `Resume` / `TogglePause` / `RestartAsync` 及其可观察状态
- [05 帧事件与线程安全](05_帧事件与线程安全/) — 事件载荷类型、`Handled` 标志与线程模型
- [06 验证与完整代码](06_验证与完整代码/) — 覆盖该特性的演示与测试、可运行的单文件程序、运行声明
