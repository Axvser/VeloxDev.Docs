# Tickable — 快速开始

**Tickable** 特性把 Unity 风格的帧循环带进普通 .NET：不需要 Unity，也不需要基类。给一个 `partial` 类标上 `[Tickable]`，Roslyn 源生成器（程序集 `VeloxDev.Core.Generator`）就会把桥接代码写进一个 `.g.cs` 文件：该类获得 `VeloxDev.TimeLine.ITickable` 实现，以及五个生命周期钩子 —— `Awake`、`Start`、`Update`、`LateUpdate`、`FixedUpdate`。它们声明为 `partial void`，由你在类的另一半里补全。

运行期由静态门面 `VeloxDev.TimeLine.TickManager` 驱动具名**通道**。一个通道拥有两条泵：

- **update 泵** —— 每帧调用一次 `Update`，随后对每个已注册行为调用一次 `LateUpdate`，节奏由目标帧率决定（默认 60）；
- **fixed-update 泵** —— 固定步长的 `FixedUpdate`，默认每 16 ms 一次；错过的步会被记账并补还。

两条泵运行在名为 `VeloxDev.Update[<通道>]` / `VeloxDev.FixedUpdate[<通道>]` 的后台线程上；平台无法启动 `Thread` 时（浏览器/WASM、iOS）改用 `async` 任务，由 `TickManager.UseAsyncLoop` 选择。两条泵都 park 在同一个共享时间源 —— 通道的 *bus* 上，所以一次 `TickManager.Pause(name)` 会同时冻结帧回调与锚定在同一时钟上的动画。

## 子页面

| 页面 | 内容 |
|---|---|
| [前置条件](00_前置条件/index.md) | 声明的目标框架、SDK，以及「无服务、无适配器、无配置」说明 |
| [安装](01_安装/index.md) | 添加 `VeloxDev.Core` 与 `VeloxDev.Core.Generator` 分析器 |
| [定义行为](02_定义行为/index.md) | `[Tickable]` 类、`channel` / `fps` 参数，以及生成的五个钩子 |
| [配置并运行循环](03_配置并运行循环/index.md) | `Start` / `StopAsync`、通道参数、状态查询与通道事件 |
| [暂停、恢复与重启](04_暂停恢复与重启/index.md) | `Pause` / `Resume` / `TogglePause` / `RestartAsync` 及其状态 |
| [帧事件与线程安全](05_帧事件与线程安全/index.md) | `FrameEventArgs`、`Handled` 标志与线程模型 |
| [验证与完整代码](06_验证与完整代码/index.md) | 完整可运行程序与运行声明 |

## 大致形状

```csharp
using VeloxDev.TimeLine;

[Tickable("demo", 60)]          // 通道 "demo"，60 fps
public partial class BouncingBall
{
    partial void Awake() { }                      // 注册时一次
    partial void Start() { }                      // 紧接 Awake，一次
    partial void Update(FrameEventArgs e) { }        // 每帧
    partial void LateUpdate(FrameEventArgs e) { }    // 每帧，在所有 Update 之后
    partial void FixedUpdate(FrameEventArgs e) { }   // 默认每 16 ms
}
```

其余一切 —— 实现 `ITickable`、转发各钩子、在通道上注册 —— 都是生成的。留给你的只有 `InitializeTickable()`、那些 `TickManager` 调用，以及你在意的钩子函数体。

## 证据来源

- **示例（主要）：** `Examples/Tickable/WPF/Demo/` —— `MainWindow.Hooks.cs` 是 `[Tickable]` 类，`SimState.cs` 是共享状态，`MainWindow.xaml.cs` 是轮询它的窗口。
- **测试（次要）：** `Src/Core/VeloxDev.Core.Test/TimeLine/` —— `TickManagerTests.cs`、`TickableAttributeTests.cs`、`TickableBusTests.cs`、`TimeLineEventArgsTests.cs`。
- **源码：** `Src/Core/VeloxDev.Core/TimeLine/` 与 `Src/Core/VeloxDev.Core/Interfaces/Tickable/`。
