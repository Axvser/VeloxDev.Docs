# Tickable — 快速开始

**tickable** 特性把 Unity 风格的帧循环带到纯 .NET —— 不需要 Unity，也不需要继承任何基类。你给一个 `partial` 类打上 `[Tickable]`，Roslyn 源生成器（位于程序集 `VeloxDev.Core.Generator`）就把桥接写进 `.g.cs`：该类获得 `VeloxDev.TimeLine.ITickable` 的实现，以及五个以 `partial void` 声明的生命周期钩子 —— `Awake`、`Start`、`Update`、`LateUpdate`、`FixedUpdate` —— 由你在类的另一半自行实现。没有可重写的 `OnFrame` 虚方法，没有 `[Update]` 方法特性，也没有东西需要继承：钩子方法本身就是 API。

运行期由静态门面 `VeloxDev.TimeLine.TickManager` 驱动多个具名**通道（channel）**。每个通道拥有两个泵：

- **Update 泵** —— 每帧为每个已注册行为调用一次 `Update`，随后调用一次 `LateUpdate`；节奏由目标帧率控制（默认 60）；
- **FixedUpdate 泵** —— 固定步长的 `FixedUpdate`，默认每 16 ms 一次；欠下的每一步都会记账，并在它自己的线程上补还。

两个泵运行在名为 `VeloxDev.Update[<通道名>]` / `VeloxDev.FixedUpdate[<通道名>]` 的后台线程上；当平台禁止 `Thread`（浏览器/WASM、iOS NativeAOT）时改由 `async` 任务驱动，由 `TickManager.UseAsyncLoop` 选择。两者都 park 在同一个时间源 —— 通道的 *bus* —— 上，所以一次 `TickManager.Pause(名字)` 会同时冻结帧回调与锚定到同一时钟上的动画。

命名沿革：该能力在 2026-10-01 之前叫 *monobehaviour*，Wiki 目录曾是 `06_monobehaviour` / `06_MonoBehaviour`。命名空间 `VeloxDev.TimeLine` 从未改变，改变的是类型名与成员名。完整的名称对照表见 API 参考。**生命周期钩子名没有改变** —— `Awake` / `Start` / `Update` / `LateUpdate` / `FixedUpdate` 与以往完全一致。

## 快速开始 — 子页面

本指南逐步导向最后一页那个可运行的单文件程序，请按顺序阅读。

| 页面 | 内容 |
|---|---|
| [00 前置条件](00_前置条件/index.md) | 支持的目标框架、SDK/运行时，以及「无需服务、无需适配器、无需配置」的说明 |
| [01 安装依赖](01_安装依赖/index.md) | 添加 `VeloxDev.Core` 包与 `VeloxDev.Core.Generator` 分析器 |
| [02 定义行为](02_定义行为/index.md) | `[Tickable]` 类、`channel` / `fps` 参数，以及生成的五个钩子 |
| [03 运行与配置循环](03_运行与配置循环/index.md) | `Start` / `StopAsync`、通道配置旋钮、状态查询与通道事件 |
| [04 暂停恢复与重启](04_暂停恢复与重启/index.md) | `Pause` / `Resume` / `TogglePause` / `RestartAsync` 及其产生的状态 |
| [05 帧事件与线程安全](05_帧事件与线程安全/index.md) | `FrameEventArgs`、`Handled` 标志与线程模型 |
| [06 验证与完整代码](06_验证与完整代码/index.md) | 完整可运行程序、验证步骤与运行声明 |

## 大致长这样

```csharp
using VeloxDev.TimeLine;

[Tickable("demo", 60)]          // 通道 "demo"，60 帧
public partial class BouncingBall
{
    partial void Awake() { }            // 注册时一次
    partial void Start() { }            // 紧随 Awake 之后一次
    partial void Update(FrameEventArgs e) { }        // 每帧
    partial void LateUpdate(FrameEventArgs e) { }    // 每帧，在所有 Update 之后
    partial void FixedUpdate(FrameEventArgs e) { }   // 默认每 16 ms
}
```

其余一切 —— 实现 `ITickable`、转发每个钩子、注册到通道 —— 都是生成的。本指南剩下的部分讲的，就是真正属于你的那几行：`InitializeTickable()`、若干 `TickManager` 调用，以及你关心的钩子函数体。

## 证据来源

- **演示（主要证据）**：`Examples/Tickable/WPF/Demo/` —— `MainWindow.Hooks.cs` 存放 `[Tickable]` 类，`SimState.cs` 存放共享状态，`MainWindow.xaml.cs` 是轮询它的窗口。
- **测试（次要证据）**：`Src/Core/VeloxDev.Core.Test/TimeLine/` —— `TickManagerTests.cs`、`TickableAttributeTests.cs`、`TickableBusTests.cs`、`TimeLineEventArgsTests.cs`。
- **源码**：`Src/Core/VeloxDev.Core/TimeLine/` 与 `Src/Core/VeloxDev.Core/Interfaces/Tickable/`。
