# MonoBehaviour — 验证与完整代码

## 1. 用演示验证

该特性附带一个 GUI 演示，`Examples/MonoBehaviour/WPF/Demo`（`net10.0-windows`）。其 `MainWindow.xaml.cs` 展示了本特性在 WPF 中的真实形态：`MainWindow` 自身就是 `[MonoBehaviour]`，其内部还含三个嵌套的 `[MonoBehaviour] private partial class` 组件（`PhysicsComponent`、`InputComponent`、`RenderComponent`），各自在构造函数中调用 `InitializeMonoBehaviour()`。窗口启动默认通道（`MonoBehaviourManager.Start()`），订阅自己的 `Update` / `FixedUpdate` 钩子，并在每帧用 `Dispatcher.Invoke` 把实时统计编组到 WPF dispatcher —— 因为钩子运行在循环线程上。窗口上的按钮调用 `Start`、`Pause`、`Resume` 与 `await StopAsync`；在按住 Left Ctrl 时按下 H 会弹出统计 `MessageBox`。

**预期结果：** 运行期间状态文本持续跳动，暂停时冻结；“Add Component” 添加的组件会在下一帧加入循环（注册被入队，正如[定义行为](../02_定义行为/)页所述）。

## 2. 用自动化测试验证

无头测试位于 `Src/Core/VeloxDev.Core.Test/TimeLine/`：

- `MonoBehaviourAttributeTests.cs` —— 特性仅作用于类、不 `AllowMultiple`、不 `Inherited`，且可用无参构造。
- `MonoBehaviourManagerTests.cs` —— `[DoNotParallelize]`，因为管理器持有共享的静态通道状态。它固定了 `SetUseAsyncLoop` / `ClearUseAsyncLoopOverride` 契约：覆盖可在通道启动前设置（或清除）、停止后可设置（或清除），但若通道已在运行则抛 `InvalidOperationException`，且该规则按通道隔离。
- `TimeLineEventArgsTests.cs` —— `FrameEventArgs` 的默认值（`DeltaTime`/`TotalTime` 为零、`CurrentFPS`/`TargetFPS` 为零、`Handled` 为 false）、空 `TransitionEventArgs`，以及 `ThreadSafeFrameEventArgs.Handled` 在 100 个并发读写任务下不抛异常。

**预期结果：** `dotnet test` 在 `VeloxDev.Core.Test` 上把 `TimeLine` 测试全部跑绿。

## 3. 完整代码

一个自包含的控制台程序。它在 `"game"` 通道上注册一个 `[MonoBehaviour]` 计数器，订阅通道事件，启动循环，证明暂停会停住两个泵，随后恢复、报告实时统计、重启，最后停止。所有 `using` 指令显式给出；唯一的外部要求是引用 `VeloxDev.Core`（见[安装依赖](../01_安装依赖/)页）：

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

namespace MonoQuickStart
{
    // 一个注册在 "game" 通道、请求 60 FPS 的行为。
    // 生成器合成 IMonoBehaviour 桥接与 partial 钩子。
    [MonoBehaviour(channel: "game", fps: 60)]
    public partial class FrameCounter
    {
        public long UpdateCount;
        public long FixedUpdateCount;

        public FrameCounter() => InitializeMonoBehaviour();   // 把当前实例注册到 "game"

        partial void Awake() => Console.WriteLine("[Awake] behaviour registered");

        partial void Start() => Console.WriteLine("[Start] loop is running");

        partial void Update(FrameEventArgs e)
        {
            Interlocked.Increment(ref UpdateCount);
        }

        partial void LateUpdate(FrameEventArgs e)
        {
        }

        partial void FixedUpdate(FrameEventArgs e)
        {
            Interlocked.Increment(ref FixedUpdateCount);
        }
    }

    public static class Program
    {
        public static async Task Main()
        {
            MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine($"[OnChannelStarted] {e.ChannelName}");
            MonoBehaviourManager.OnChannelStopped += (s, e) => Console.WriteLine($"[OnChannelStopped] {e.ChannelName}");

            MonoBehaviourManager.SetFixedUpdateInterval(16, "game");   // fixed-update 泵每 16 ms 跳动一次

            var counter = new FrameCounter();     // 注册到 "game" 通道（入队，直到循环启动）
            Console.WriteLine("SystemStatus (before Start): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("ActiveBehaviorCount (before Start): " + MonoBehaviourManager.ActiveBehaviorCount("game"));

            MonoBehaviourManager.Start("game");
            await Task.Delay(120);               // 加入队列在帧首被清空

            Console.WriteLine("SystemStatus (running): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("ActiveBehaviorCount (running): " + MonoBehaviourManager.ActiveBehaviorCount("game"));

            // 暂停：Update 与 FixedUpdate 两个泵都不再前进。
            MonoBehaviourManager.Pause("game");
            Console.WriteLine("SystemStatus (paused): " + MonoBehaviourManager.SystemStatus("game"));
            long a = Volatile.Read(ref counter.UpdateCount);
            await Task.Delay(300);
            long b = Volatile.Read(ref counter.UpdateCount);
            Console.WriteLine($"Updates grew while paused: {b - a}");

            MonoBehaviourManager.Resume("game");
            Console.WriteLine("SystemStatus (resumed): " + MonoBehaviourManager.SystemStatus("game"));

            await Task.Delay(800);
            Console.WriteLine($"UpdateCount: {Volatile.Read(ref counter.UpdateCount)}");
            Console.WriteLine($"FixedUpdateCount: {Volatile.Read(ref counter.FixedUpdateCount)}");
            Console.WriteLine($"CurrentFPS: {MonoBehaviourManager.CurrentFPS("game")}");
            Console.WriteLine($"TotalFrames: {MonoBehaviourManager.TotalFrames("game")}");
            Console.WriteLine($"TotalTimeMs: {MonoBehaviourManager.TotalTimeMs("game")}");
            Console.WriteLine($"IsUpdateThreadAlive: {MonoBehaviourManager.IsUpdateThreadAlive("game")}");

            // 重启 = 停止 + 清空统计/队列 + 在同一通道上再次启动。
            await MonoBehaviourManager.RestartAsync("game");
            await Task.Delay(120);
            Console.WriteLine("SystemStatus (after restart): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("ActiveBehaviorCount (after restart): " + MonoBehaviourManager.ActiveBehaviorCount("game"));
            Console.WriteLine("TotalFrames (right after restart): " + MonoBehaviourManager.TotalFrames("game"));

            await MonoBehaviourManager.StopAsync("game");
            Console.WriteLine("SystemStatus (after stop): " + MonoBehaviourManager.SystemStatus("game"));
            Console.WriteLine("TotalFrames (after stop): " + MonoBehaviourManager.TotalFrames("game"));
            Console.WriteLine("IsUpdateThreadAlive (after stop): " + MonoBehaviourManager.IsUpdateThreadAlive("game"));
        }
    }
}
```

无 `...` —— 每个标识符都在上面定义，或由显式 `using` 指令解析。下面的文本是一次 `Release` 运行的记录输出；计数器与计时值因机器而异，但顺序与状态转换在各次运行间稳定：

```text
SystemStatus (before Start): Stopped
ActiveBehaviorCount (before Start): 0
[OnChannelStarted] game
[Awake] behaviour registered
[Start] loop is running
SystemStatus (running): Running
ActiveBehaviorCount (running): 1
SystemStatus (paused): Paused
Updates grew while paused: 0
SystemStatus (resumed): Running
UpdateCount: 31
FixedUpdateCount: 33
CurrentFPS: 24
TotalFrames: 30
TotalTimeMs: 1240
IsUpdateThreadAlive: True
[OnChannelStopped] game
[OnChannelStarted] game
SystemStatus (after restart): Running
ActiveBehaviorCount (after restart): 1
TotalFrames (right after restart): 4
[OnChannelStopped] game
SystemStatus (after stop): Stopped
TotalFrames (after stop): 0
IsUpdateThreadAlive (after stop): False
```

对照各页来读这段文本：

- `ActiveBehaviorCount (before Start): 0` → `[Awake]` / `[Start]` → `ActiveBehaviorCount (running): 1` —— 注册被入队，只有循环首帧清空加入队列后才被拾取（[定义行为](../02_定义行为/)页与[运行与配置循环](../03_运行与配置循环/)页）。
- `Updates grew while paused: 0` —— `Pause` 停住两个泵（[暂停恢复与重启](../04_暂停恢复与重启/)页）。
- `RestartAsync` 之后统计从接近零重新开始（`TotalFrames (right after restart): 4`），而行为保持注册、不会再次 `Awake`（同页）。
- `StopAsync` 之后 `TotalFrames (after stop): 0` 显示统计被重置，`SystemStatus` 回到 `"Stopped"`。

## 4. 运行声明

- ✅ 已于 2026-09-07 实际构建并运行（`dotnet run -c Release`，目标 `net10.0`，以项目引用方式指向本仓库 `VeloxDev.Core`）。记录输出逐字见第 3 节。两次更早的相同运行得到相同顺序与状态转换，仅时序相关数值（`FixedUpdateCount`、`TotalTimeMs`、`CurrentFPS`）有差异。
