# 帧循环

由具名时钟通道驱动对象的五个生命周期钩子。`[Tickable]` 生成 `ITickable` 样板；`TickManager` 负责线程、目标帧率、固定步长与时间缩放。

## 1. 前置条件

- **`VeloxDev.Core` 支持的目标框架**：`netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`。本示例使用 `net8.0`。
- **`VeloxDev.Core`** 与 **`VeloxDev.Core.Generator`**（分析器）。生成器发出 `partial` 钩子声明与 `ITickable` 实现。
- .NET SDK 8.0 或更高。无需服务或 GUI。

## 2. 安装/引入依赖

```text
dotnet new console -n TickQuickStart
cd TickQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 两个包还原成功。首次构建后即可使用 `InitializeTickable`、`CloseTickable` 与五个 `Invoke*` 方法；设置 `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` 可把 `*_Tick.g.cs` 写到 `obj/` 下。

## 3. 基础配置/注册

特性指定通道，并可指定目标帧率。类需要 `partial`，因为生成器要补上 `ITickable` 成员与分部钩子声明。

```csharp
using VeloxDev.TimeLine;

[Tickable("quickstart", fps: 60)]
public partial class Ticker
{
    partial void Awake() => System.Console.WriteLine("Awake");
    partial void Start() => System.Console.WriteLine("Start");
    partial void Update(FrameEventArgs e) { }
    partial void LateUpdate(FrameEventArgs e) { }
    partial void FixedUpdate(FrameEventArgs e) { }
}
```

**预期结果：** `new Ticker()` 已经实现 `ITickable`。`fps` 不小于 1 时，`InitializeTickable()` 会设置该通道的目标帧率并注册对象。

## 4. 核心用法（逐步构建）

### 4.1 注册、启动、停止

```csharp
var ticker = new Ticker();
ticker.InitializeTickable();
TickManager.Start("quickstart");

// 之后
await TickManager.StopAsync("quickstart");
ticker.CloseTickable();
```

注册只是把生命周期入队；通道会在第一帧体之前排空它。`Start` 是幂等的。`CloseTickable()` 取消注册；再次注册同一对象会在新的包装上重跑 `Awake`/`Start`。

**预期结果：** 第一帧之前先打印一次 `Awake`，再打印一次 `Start`。

### 4.2 五个钩子与各自的时钟

- `Awake` 与 `Start` 每次注册各运行一次，在第一帧之前。
- `Update` 每帧一次，运行在通道的 update 线程上，`DeltaTime` 可变。
- `LateUpdate` 在同一线程的 `Update` 之后运行，除非 `Update` 置了 `e.Handled`。
- `FixedUpdate` 运行在 fixed-update 线程上，`DeltaTime` 固定，每个欠下的步调用一次；卡顿会在一次唤醒中以多次调用补还。

`FrameEventArgs` 还携带 `TotalTime`、`CurrentFPS` 与 `TargetFPS`。一帧内所有钩子复用同一个实例，因此钩子不能保留它。

**预期结果：** 同时存在两者的帧里，`Update` 在 `LateUpdate` 之前；`FixedUpdate` 与帧数无关。

### 4.3 抑制本帧剩余钩子

```csharp
partial void Update(FrameEventArgs e)
{
    if (++_frames == 3)
    {
        e.Handled = true;   // 本帧不再执行后续 Update 体，也不执行 LateUpdate
    }
}
```

引擎在钩子之间读取 `Handled`。它不影响 `FixedUpdate`，后者每个步都自建事件参数。

**预期结果：** 第 3 帧不运行 `LateUpdate`；第 4 帧恢复。

### 4.4 通道控制

```csharp
TickManager.SetTargetFPS(30, "quickstart");
TickManager.SetFixedUpdateInterval(33, "quickstart");   // 每个固定步的毫秒数
TickManager.SetTimeScale(0.5f, "quickstart");
TickManager.Pause("quickstart");
TickManager.Resume("quickstart");
TickManager.TogglePause("quickstart");
await TickManager.RestartAsync("quickstart");
```

`SetTimeScale(0f, ...)` 会冻结时钟，但它不是暂停：`IsPaused` 仍为 false，`SystemStatus` 仍报告 running。需要判断消费者停在哪个信号上时，读 `TickManager.Bus(channel)`（`IsAdvancing`、`IsPaused`、`Rate`、`Epoch`、`Position`）。

**预期结果：** 修改目标帧率会改变实测 `CurrentFPS`；时间缩放为 0 时时钟不再前进，但 `IsPaused` 不变。

### 4.5 通道与多行为

每个通道有自己的两条线程、目标帧率、固定步长与时间缩放。注册在同一通道上的行为都在该通道线程上顺序调用。`TickManager.ChannelNames`、`OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` 与 `OnBehaviorError` 暴露管理器状态；`TickManager.UseAsyncLoop` 选择循环形态，`SetUseAsyncLoop(..., channel)` 可按通道覆盖。

```csharp
TickManager.RegisterBehaviour(other, "physics");
TickManager.SetTimeScale(2f, "physics");
```

**预期结果：** 两个通道独立前进；`physics` 上的行为绝不会运行在 `quickstart` 的线程上。

## 5. 验证

运行完整程序。`Awake` 与 `Start` 各出现一次；`Update` 与 `LateUpdate` 行重复出现，但第 3 帧没有 `LateUpdate`；`FixedUpdate` 行按固定步出现。约 400 毫秒后摘要打印 `running=True` 与一个正的帧数。

## 6. 完整代码

```csharp
using System;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

var ticker = new Ticker();
ticker.InitializeTickable();
TickManager.Start("quickstart");

await Task.Delay(400);

Console.WriteLine($"running={TickManager.IsRunning("quickstart")} frames={TickManager.TotalFrames("quickstart")}");

await TickManager.StopAsync("quickstart");
ticker.CloseTickable();

[Tickable("quickstart", fps: 60)]
public partial class Ticker
{
    private int _frames;

    partial void Awake() => Console.WriteLine("Awake");
    partial void Start() => Console.WriteLine("Start");

    partial void Update(FrameEventArgs e)
    {
        _frames++;
        if (_frames <= 3)
        {
            Console.WriteLine($"Update #{_frames} dt={e.DeltaTime.TotalMilliseconds:F1} ms fps={e.CurrentFPS}");
        }

        if (_frames == 3)
        {
            e.Handled = true;
        }
    }

    partial void LateUpdate(FrameEventArgs e)
    {
        if (_frames <= 4)
        {
            Console.WriteLine($"LateUpdate after Update #{_frames}");
        }
    }

    partial void FixedUpdate(FrameEventArgs e)
    {
        if (_frames <= 3)
        {
            Console.WriteLine($"FixedUpdate dt={e.DeltaTime.TotalMilliseconds:F1} ms");
        }
    }
}
```

钩子顺序、`Handled` 行为与通道控制与 `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs`、`MainWindow.xaml.cs` 一致。

## 7. 运行声明

- ⚠️ 未实际运行——仅于 2026-11-25 静态核验。已对照 `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs`、`TickableAttribute.cs`、`FrameEventArgs.cs`、`TimeLineEventArgs.cs`、`Src/Core/VeloxDev.Core/Interfaces/Tickable/ITickable.cs`、`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` 以及 WPF 帧循环 demo 核验。本环境未执行构建。
