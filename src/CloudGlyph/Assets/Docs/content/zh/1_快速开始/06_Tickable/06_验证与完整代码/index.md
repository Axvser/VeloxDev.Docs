# 06 · 验证与完整代码

## 1. 复现这个程序

创建一个控制台工程，按 `01_安装依赖` 添加两个包，然后把 `Program.cs` 换成第 3 节的清单。接着：

```text
dotnet run -c Debug
```

**预期结果：** 十一行输出，下面每一行主张都对应其中一行（有两行读的是同一行 `running`）。全程无需交互，也不需要窗口。

## 2. 每一行证明了什么

| 行 | 主张 | 行内的证据 |
|---|---|---|
| `[event] OnChannelStarted -> demo` | 生命周期事件是按通道区分的 | `TickChannelEventArgs.ChannelName` |
| `[Awake]` 早于 `[Start]` 早于 `running` | `Awake` / `Start` 在排空时运行，先于第一帧帧体 | 它们在任何 `Update` 计数变动之前打印 |
| `running … ActiveBehaviorCount=1` | 注册确实到达了通道 | `TickManager.ActiveBehaviorCount("demo")` |
| `running … Update=n LateUpdate=n Fixed≈1.7n` | 定步长泵按自己的节奏运行，与帧率脱钩 | 步长 16 ms 意味着固定泵以约 62.5 Hz 独立于目标帧率运行。在这 400 ms 窗口内 update 泵只跑到约 37 Hz（循环还在起步），所以比值是 1.7 而不是稳定 60 fps 时的约 1.04。跑久一点，第二个数会向第一个数收敛 |
| `paused … IsUpdateThreadAlive=True` | park 住的泵是活着的，不是死的 | 存活查询看的是时钟而不是活动 |
| `paused … framesDelta=1` | 一帧已在途的帧仍会落下 | 本程序在 `Pause` 返回之后才开始读数 |
| `resumed … framesDelta=6` | 恢复重新开始交付 | 严格大于暂停时的读数 |
| `rate TimeScale=2` | `SetTimeScale` 直达时钟 | 通过 `TickManager.TimeScale` 读回 |
| `handled Update +n LateUpdate +0` | `Handled` 跳过整个剩余的 `LateUpdate` 阶段 | `Update` 照跑，`LateUpdate` 未跑 |
| `fps TargetFPS=30 measured=31` | 目标帧率生效 | 实测值来自墙钟，不来自设置本身 |
| `bus IsAdvancing=True Rate=2 …` | 通道暴露了它的时钟 | `TickManager.Bus("demo")` 就是那个 `ITimeSourceControl` |
| `stopped … threadAliveAfter=False` | 两个泵都停了，统计也重置了 | `IsRunning` 为 false，`SystemStatus` 为 `"Stopped"` |

计数器在两次运行之间会有一两帧的浮动 —— 它们是对真实循环的测量，不是常量。

## 3. 完整代码

`Program.cs` —— 单文件、无省略号，每个标识符都在此定义或由分析器生成。

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

        ball.InitializeTickable();                 // 生成的方法：SetTargetFPS(60) + RegisterBehaviour
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
        await Task.Delay(1100);   // CurrentFPS 每墙钟秒才重新发布一次
        Console.WriteLine($"fps       TargetFPS={TickManager.TargetFPS("demo")} measured={TickManager.CurrentFPS("demo")}");

        var bus = TickManager.Bus("demo");
        Console.WriteLine($"bus       IsAdvancing={bus?.IsAdvancing} Rate={bus?.Rate} Position={bus?.Position.TotalMilliseconds:F0}ms");

        var alive = TickManager.IsUpdateThreadAlive("demo");
        ball.CloseTickable();                      // 生成的方法：UnregisterBehaviour
        TickManager.UnregisterBehaviour(ball);
        await TickManager.StopAsync("demo");
        Console.WriteLine($"stopped   IsRunning={TickManager.IsRunning("demo")} " +
                          $"SystemStatus={TickManager.SystemStatus("demo")} " +
                          $"threadAliveBefore={alive} threadAliveAfter={TickManager.IsUpdateThreadAlive("demo")}");
    }
}
```

## 4. 再对照随仓库附带的演示与测试

仓库里有一个 GUI 演示与一套测试，覆盖同一个表面。用下面的命令在你自己的检出上运行它们。

**WPF 演示** —— `Examples/Tickable/WPF/Demo/`，一个把自己注册为 `default` 通道上唯一行为的窗口，并打印两个泵交付了什么（`MainWindow.Hooks.cs`、`SimState.cs`、`MainWindow.xaml.cs`）：

```text
cd Examples/Tickable/WPF/Demo
dotnet build Demo.csproj -c Debug
```

**测试套件** —— `Src/Core/VeloxDev.Core.Test/TimeLine/`：

```text
cd Src/Core/VeloxDev.Core.Test
dotnet test --filter "FullyQualifiedName~TimeLine"
```

`FullyQualifiedName~TimeLine` 是对完全限定名的子串匹配，因此它选中的不止 `Src/Core/VeloxDev.Core.Test/TimeLine/` 下的四个文件（共 **31** 个 `[TestMethod]`：TickManagerTests 11、TickableBusTests 12、TimeLineEventArgsTests 6、TickableAttributeTests 2）。它还会命中 timing 与 TransitionSystem 套件中**方法名**含 `Timeline` 的 15 个测试 —— `Timeline_*`、`Seek_*`、`SetRate_*`、`Loop_TakesTheDeclaredDuration`、`SharedTimeline_PausesBothAnimationsAtOnce`、`Switch_EveryTargetIsAnchoredToTheSameTimeline`。31 + 15 = 46。

**预期结果：** `失败: 0，通过: 46，已跳过: 0，总计: 46`。

## 5. 运行声明

- ✅ **2026-10-01 实际构建并运行。** 第 3 节的程序以 `dotnet run -c Debug`（net10.0、.NET SDK 10、Windows 11）编译并执行，依赖的是本仓库 HEAD 构建出的 `VeloxDev.Core` 与 `VeloxDev.Core.Generator` 分析器。记录输出：

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

- ✅ `Examples/Tickable/WPF/Demo/Demo.csproj` 构建成功：`已成功生成。 0 个警告 0 个错误`。演示**未**被启动 —— 它是一个没有控制台输出的 GUI 窗口，`dotnet build` 就是它能提供的证据上限。
- ✅ **测试套件已于 2026-10-01 执行。** `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~TimeLine"` → `已通过! - 失败: 0，通过: 46，已跳过: 0，总计: 46，持续时间: 8 s - VeloxDev.Core.Test.dll (net10.0)`。该过滤器是子串匹配，所以这 46 个 = `TimeLine/` 下的 31 个 + timing / TransitionSystem 中方法名含 `Timeline` 的 15 个。
- ⚠️ 第 1、2 节的每条预期结果都由上面这段记录支撑。帧数与步数在两次运行之间会差一两下；记录的是其中一次的数值，不是契约。
