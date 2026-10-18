# 验证与完整代码

## 1. 复现程序

创建一个控制台项目，添加 `01_安装` 中的两个包，并用第 3 节的清单替换 `Program.cs`。然后：

```text
dotnet run -c Debug
```

**预期结果：** 输出十一行。每行都由下表的一行认领；其中三行读的是同一行 `running`。

## 2. 每一行证明了什么

| 输出行 | 结论 | 行内证据 |
|---|---|---|
| `[event] OnChannelStarted -> demo` | 生命周期事件是通道范围的 | `TickChannelEventArgs.ChannelName` |
| `[Awake]` 在 `[Start]` 之前，`[Start]` 在 `running` 之前 | `Awake` / `Start` 在排空时、第一帧帧体之前运行 | 它们在任何 `Update` 计数增长之前打印 |
| `running … ActiveBehaviorCount=1` | 注册到达了通道 | `TickManager.ActiveBehaviorCount("demo")` |
| `running … Update=n LateUpdate=n Fixed≈1.7n` | fixed 泵按自己的节奏运行，与帧率解耦 | 步长为 16 ms，所以 fixed 泵约 62.5 Hz，与目标帧率无关。在这个 400 ms 窗口里 update 泵仍在爬升，只达到约 37 Hz，所以比值约 1.7，而不是稳定 60 fps 通道的约 1.04。运行更久会收敛 |
| `paused … IsUpdateThreadAlive=True` | park 住的泵是活的，不是死的 | 存活查询限定的是时钟，不是活动 |
| `paused … framesDelta=1` | 已有一帧在途并落地 | 在暂停返回**之后**测量，本例正是如此 |
| `resumed … framesDelta=6` | 恢复重新开始交付 | 严格大于暂停时的读数 |
| `rate TimeScale=2` | `SetTimeScale` 写穿到时钟 | 通过 `TickManager.TimeScale` 读回 |
| `handled Update +n LateUpdate +0` | `Handled` 跳过剩余的整个 `LateUpdate` 阶段 | `Update` 仍运行，`LateUpdate` 没有 |
| `fps TargetFPS=30 measured=31` | 目标生效 | 实测值来自墙钟，不是配置值 |
| `bus IsAdvancing=True Rate=2 …` | 通道暴露了它的时钟 | `TickManager.Bus("demo")` 是 `ITimeSourceControl` |
| `stopped … threadAliveAfter=False` | 两条泵都已停止，统计已重置 | `IsRunning` 为 false，`SystemStatus` 为 `"Stopped"` |

计数器会在多次运行间波动一两帧 —— 它们是对真实循环的测量，不是常量。

## 3. 完整代码

`Program.cs` —— 单文件，无省略号，每个标识符都在此定义或由分析器生成。

```csharp
using VeloxDev.TimeLine;

namespace TickVerify;

// 完整的快速开始行为：一个 partial 类，五个生成的钩子。
[Tickable("demo", 60)]
public partial class BouncingBall
{
    private double _height;
    private double _velocity;
    private readonly object _gate = new();

    public int Updates { get; private set; }
    public int LateUpdates { get; private set; }
    public int FixedSteps { get; private set; }
    public bool FreezeLateUpdate { get; set; }

    public double Height { get { lock (_gate) return _height; } }
    public double Velocity { get { lock (_gate) return _velocity; } }

    partial void Awake() => Console.WriteLine("[Awake]   registration drained; Update has run 0 times");

    partial void Start() => Console.WriteLine("[Start]   next call is the first frame body");

    partial void Update(FrameEventArgs e)
    {
        lock (_gate)
        {
            _velocity += 1.2 * e.DeltaTime.TotalSeconds;
            _height += _velocity * e.DeltaTime.TotalSeconds;
            if (_height >= 1.5)
            {
                _height = 0;
                _velocity = 0;
            }
        }

        Updates++;

        if (FreezeLateUpdate)
            e.Handled = true;
    }

    partial void LateUpdate(FrameEventArgs e) => LateUpdates++;

    partial void FixedUpdate(FrameEventArgs e)
    {
        lock (_gate)
        {
            _velocity += 1.2 * e.DeltaTime.TotalSeconds;
            _height += _velocity * e.DeltaTime.TotalSeconds;
            if (_height >= 1.5)
            {
                _height = 0;
                _velocity = 0;
            }
        }

        FixedSteps++;
    }
}

public static class Program
{
    public static async Task Main()
    {
        var ball = new BouncingBall();

        TickManager.OnChannelStarted += (_, e) => Console.WriteLine($"[event]   OnChannelStarted -> {e.ChannelName}");

        ball.InitializeTickable();                 // 生成：SetTargetFPS(60) + RegisterBehaviour
        TickManager.Start("demo");

        await Task.Delay(400);
        Console.WriteLine($"running   IsRunning={TickManager.IsRunning("demo")} " +
                          $"SystemStatus={TickManager.SystemStatus("demo")} " +
                          $"TargetFPS={TickManager.TargetFPS("demo")} " +
                          $"ActiveBehaviorCount={TickManager.ActiveBehaviorCount("demo")} " +
                          $"Update={ball.Updates} LateUpdate={ball.LateUpdates} Fixed={ball.FixedSteps}");

        TickManager.Pause("demo");
        var framesAtPause = TickManager.TotalFrames("demo");
        await Task.Delay(120);
        Console.WriteLine($"paused    IsPaused={TickManager.IsPaused("demo")} " +
                          $"framesDelta={TickManager.TotalFrames("demo") - framesAtPause} " +
                          $"IsUpdateThreadAlive={TickManager.IsUpdateThreadAlive("demo")}");

        TickManager.Resume("demo");
        await Task.Delay(150);
        Console.WriteLine($"resumed   framesDelta={TickManager.TotalFrames("demo") - framesAtPause} (must be > 0)");

        TickManager.SetTimeScale(2f, "demo");
        Console.WriteLine($"rate      TimeScale={TickManager.TimeScale("demo")}");

        ball.FreezeLateUpdate = true;
        var lateBefore = ball.LateUpdates;
        var updatesBefore = ball.Updates;
        await Task.Delay(200);
        Console.WriteLine($"handled   Update +{ball.Updates - updatesBefore} LateUpdate +{ball.LateUpdates - lateBefore} (must be +0)");
        ball.FreezeLateUpdate = false;

        TickManager.SetTargetFPS(30, "demo");
        await Task.Delay(1100);   // CurrentFPS 每墙钟秒重新发布一次
        Console.WriteLine($"fps       TargetFPS={TickManager.TargetFPS("demo")} measured={TickManager.CurrentFPS("demo")}");

        var bus = TickManager.Bus("demo");
        Console.WriteLine($"bus       IsAdvancing={bus?.IsAdvancing} Rate={bus?.Rate} Position={bus?.Position.TotalMilliseconds:F0}ms");

        var alive = TickManager.IsUpdateThreadAlive("demo");
        ball.CloseTickable();                      // 生成：UnregisterBehaviour
        await TickManager.StopAsync("demo");
        Console.WriteLine($"stopped   IsRunning={TickManager.IsRunning("demo")} " +
                          $"SystemStatus={TickManager.SystemStatus("demo")} " +
                          $"threadAliveBefore={alive} threadAliveAfter={TickManager.IsUpdateThreadAlive("demo")}");
    }
}
```

## 4. 同时对照仓库中的示例与测试

**WPF 示例** —— `Examples/Tickable/WPF/Demo/`，一个把自己注册为 `default` 通道唯一行为的窗口，并显示两条泵交付了什么（`MainWindow.Hooks.cs`、`SimState.cs`、`MainWindow.xaml.cs`）：

```text
cd Examples/Tickable/WPF/Demo
dotnet build Demo.csproj -c Debug
```

**测试套件** —— `Src/Core/VeloxDev.Core.Test/TimeLine/`：

```text
cd Src/Core/VeloxDev.Core.Test
dotnet test --filter "FullyQualifiedName~TimeLine"
```

`FullyQualifiedName~TimeLine` 是子串匹配，因此会选中 `Src/Core/VeloxDev.Core.Test/TimeLine/` 下的 28 个 `[TestMethod]`（TickableBusTests 12、TickManagerTests 11、TimeLineEventArgsTests 3、TickableAttributeTests 2），再加上 15 个名字含 `Timeline` 或匹配同一子串的 timing / TransitionSystem 测试。28 + 15 = 43。

**预期结果：** `Failed: 0, Passed: 43, Skipped: 0, Total: 43`。

## 5. 运行声明

- ⚠️ **本次修订未执行第 3 节的控制台程序。** 它是对写作时源码的静态核对：其中用到的每个类型、成员与签名都存在于 `Src/Core/VeloxDev.Core/TimeLine/`、`Src/Core/VeloxDev.Core/Interfaces/Tickable/` 与 `Writers/TickWriter.cs`。下面那段记录来自 2026-10-01，仅作为期望形状保留，不是本次修订的输出。计数器会因运行不同而波动一两帧。
- ✅ **测试套件于 2026-10-18 执行。** `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~TimeLine"` → `已通过! - 失败: 0，通过: 43，已跳过: 0，总计: 43，持续时间: 8 s - VeloxDev.Core.Test.dll (net10.0)`（`Passed! - Failed: 0, Passed: 43, Skipped: 0, Total: 43`，8 秒）。
- ✅ `Examples/Tickable/WPF/Demo/Demo.csproj` 于 2026-10-01 构建成功：`已成功生成。 0 个警告 0 个错误`。示例**未**启动 —— 它是没有控制台输出的 GUI 窗口，`dotnet build` 是它能提供的证据上限。

2026-10-01 第 3 节的记录：

```text
[event]   OnChannelStarted -> demo
[Awake]   registration drained; Update has run 0 times
[Start]   next call is the first frame body
running   IsRunning=True SystemStatus=Running TargetFPS=60 ActiveBehaviorCount=1 Update=15 LateUpdate=15 Fixed=26
paused    IsPaused=True framesDelta=1 IsUpdateThreadAlive=True
resumed   framesDelta=6 (must be > 0)
rate      TimeScale=2
handled   Update +7 LateUpdate +0 (must be +0)
fps       TargetFPS=30 measured=31
bus       IsAdvancing=True Rate=2 Position=3240ms
stopped   IsRunning=False SystemStatus=Stopped threadAliveBefore=True threadAliveAfter=False
```
