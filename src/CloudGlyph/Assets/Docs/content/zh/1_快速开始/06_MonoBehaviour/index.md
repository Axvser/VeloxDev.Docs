# MonoBehaviour — 快速开始

## MonoBehaviour

### 快速开始

#### 1. 环境准备（Prerequisites）

- **支持目标**（来自 `VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` —— 可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK 以运行源码生成器；已在 SDK 9.0/10.0 下验证 —— *被验证过*的环境，并非要求。WPF 示例面向 `net10.0-windows`。
- **包管理器：** NuGet / `dotnet` CLI。
- **所需服务：** 无 —— 示例使用纯控制台宿主，便于在终端观察帧循环。


#### 2. 安装 / 添加依赖

```bash
dotnet add package VeloxDev.Core
```

**预期结果：** 命令以 `0` 退出；`.csproj` 中出现 `<PackageReference Include="VeloxDev.Core" />` 并完成还原。包内含运行时（`VeloxDev.TimeLine`、`VeloxDev.MonoBehaviour`），并依赖源生成器 `VeloxDev.Core.Generator`，后者在编译期把 `[MonoBehaviour]` 类变成 `IMonoBehaviour` 实现。

#### 3. 基础设置 / 注册

声明 `[MonoBehaviour] partial` 类，并在构造函数中调用 `InitializeMonoBehaviour()`。生成器会生成 `InitializeMonoBehaviour()`（内部调用 `MonoBehaviourManager.RegisterBehaviour(this, channel)`）并声明 partial 钩子 `Awake`、`Start`、`Update(FrameEventArgs)`、`LateUpdate(FrameEventArgs)`、`FixedUpdate(FrameEventArgs)`。

```csharp
using System.Threading;
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
    public int UpdateCount;
    public int FixedUpdateCount;

    public FrameCounter() => InitializeMonoBehaviour();   // 注册当前实例

    partial void Update(FrameEventArgs e)
    {
        Interlocked.Increment(ref UpdateCount);
    }
}
```

**预期结果：** 无需手写 `IMonoBehaviour` 实现即可编译 —— 生成器补齐了桥接。实例化 `FrameCounter` 即完成在 `"game"` 通道上的注册。

#### 4. 核心用法（分步进行）

**4.1 配置通道**

```csharp
MonoBehaviourManager.SetTargetFPS(60, "game");           // 钳位：1..1000
MonoBehaviourManager.SetFixedUpdateInterval(16, "game"); // 毫秒，钳位：1..1000
MonoBehaviourManager.SetTimeScale(1.0f, "game");         // 钳位：0..10
```

**预期结果：** 数值作为配置请求入队，在下一帧开始时生效；越界值被静默钳位（出处：`MonoBehaviourManager.cs` 第 184-210 行）。

**4.2 实现生命周期钩子**

```csharp
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
```

**预期结果：** `Awake` 与 `Start` 在被循环拾取时各执行一次；`Update` 与 `LateUpdate` 每帧执行；`FixedUpdate` 在固定时间线程上按 `SetFixedUpdateInterval` 毫秒（默认 16）执行。

**4.3 启动循环**

```csharp
var counter = new FrameCounter();
MonoBehaviourManager.Start("game");
```

**预期结果：** `Start` 启动 Update 与 FixedUpdate 线程（`UseAsyncLoop` 为 `true` 时改为异步任务）并触发 `OnChannelStarted`。`SystemStatus("game")` 返回 `"Running"`，`ActiveBehaviorCount("game")` 返回 `1`。

**4.4 停止循环**

```csharp
await MonoBehaviourManager.StopAsync("game");
```

**预期结果：** 两个线程被取消并汇合（带 1 秒关闭超时）、统计被重置、队列被清空，触发 `OnChannelStopped`。`SystemStatus("game")` 返回 `"Stopped"`。

#### 5. 验证

运行下方完整程序并观察帧计数器。一次示例运行输出：

```text
[Awake] behaviour registered
[Start] loop is running
SystemStatus: Running
ActiveBehaviorCount: 1
CurrentFPS: 34
TotalFrames: 49
UpdateCount: 50
FixedUpdateCount: 54
SystemStatus after stop: Stopped
```

**预期结果：** 循环运行期间 `SystemStatus` 为 `Running`；在 1.5 秒窗口内 `UpdateCount` 与 `FixedUpdateCount` 持续增长；`StopAsync` 之后状态变为 `Stopped`。

#### 6. 完整代码

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
    public int UpdateCount;
    public int FixedUpdateCount;

    public FrameCounter() => InitializeMonoBehaviour();

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
        MonoBehaviourManager.SetTargetFPS(60, "game");
        MonoBehaviourManager.SetFixedUpdateInterval(16, "game");
        MonoBehaviourManager.SetTimeScale(1.0f, "game");

        var counter = new FrameCounter();
        MonoBehaviourManager.Start("game");

        await Task.Delay(1500);

        Console.WriteLine($"SystemStatus: {MonoBehaviourManager.SystemStatus("game")}");
        Console.WriteLine($"ActiveBehaviorCount: {MonoBehaviourManager.ActiveBehaviorCount("game")}");
        Console.WriteLine($"CurrentFPS: {MonoBehaviourManager.CurrentFPS("game")}");
        Console.WriteLine($"TotalFrames: {MonoBehaviourManager.TotalFrames("game")}");
        Console.WriteLine($"UpdateCount: {counter.UpdateCount}");
        Console.WriteLine($"FixedUpdateCount: {counter.FixedUpdateCount}");

        await MonoBehaviourManager.StopAsync("game");
        Console.WriteLine($"SystemStatus after stop: {MonoBehaviourManager.SystemStatus("game")}");
    }
}
```

#### 7. 运行声明（Run Declaration）

- ✅ 已于 2026-08-17 实际构建并运行。记录到的输出（见第 5 节）：`[Awake] behaviour registered`、`[Start] loop is running`、`SystemStatus: Running`、`ActiveBehaviorCount: 1`、`CurrentFPS: 34`、`TotalFrames: 49`、`UpdateCount: 50`、`FixedUpdateCount: 54`、`SystemStatus after stop: Stopped`。
- 仓库自带的 WPF 示例（`Examples/MonoBehaviour/WPF/Demo`）未在本环境运行；上述控制台示例覆盖了相同的管理器 API（`Start`、`StopAsync`、`SetTargetFPS`、`SetFixedUpdateInterval`、`SetTimeScale`、状态查询）以及生成的生命周期钩子。
