# Workflow System — 暂停并恢复一次运行

一次编译运行就是一长串被 await 的节点驱动。`ManualExecutionGate` 是它的暂停点：引擎在每个节点驱动前 await 它，所以宿主能把运行握在节点边界上，然后再放开。在 `01_安装` 建好的 `WorkflowQuickStart` 项目里创建这个类。

## 1. 把门挂到会话上

门在会话上，不在引擎上：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var gate = new ManualExecutionGate();
var context = new RuntimeContext { ExecutionGate = gate };
```

**预期结果：** 编译通过，且 `gate.IsPaused` 为 `false`。

## 2. 握住运行

运行开始前先 `Pause()` —— 引擎到达的第一个节点边界就会阻塞：

```csharp
gate.Pause();
var run = new RuntimeEngine().RunAsync(rootGraph, context, CancellationToken.None);
await Task.Delay(80);          // 让引擎走到第一个边界
```

**预期结果：** `context.Status == "Paused"`、`gate.IsPaused == true`、`context.IsRunning == true`，而 `context.Data` 仍是 `null` —— 一个节点都没被驱动。注意第三条：**暂停不是停止**，运行仍在飞。

## 3. 放开它

```csharp
gate.Resume();
await run;

Console.WriteLine($"{context.Status} {context.Data}");
```

**预期结果：** 运行正常跑完 —— `Completed tick->bias->print`。门一放开 `Status` 就回到 `"Running"`，随后变成 `"Completed"`。

## 4. 从别处暂停一次运行中的运行

宿主的 UI 线程在运行停在调度器上时按暂停；`Pause` 与 `Resume` 从任何线程调用都安全，包括运行所在的那个：

```csharp
// demo 会话把它暴露成一个可绑定属性：
public ManualExecutionGate Gate { get; } = new();

Gate.Pause();     // 握在下一个节点边界
Gate.Resume();    // 放开
```

**预期结果：** 暂停在下一个节点边界生效，绝不发生在节点内部 —— 已经在被驱动的节点一定跑完。

## 5. 停掉一个被暂停的运行

在被握住时取消运行的令牌会让它结束，而不是挂住：

```csharp
var cts = new CancellationTokenSource();
var held = new RuntimeEngine().RunAsync(rootGraph, context, cts.Token);
gate.Pause();
await Task.Delay(50);
cts.Cancel();
await held;                                   // 会返回，不会挂住

Console.WriteLine($"{context.Status} {context.Outcome}");
```

**预期结果：** `Stopped Cancelled`。这就是 `IExecutionGate.WaitAsync` 在取消时必须**抛出**而不是返回的原因：一个「门没开却回来了」的调用方会继续驱动。

## 6. 真实仓库里它在哪

demo 把同一个门接到宿主 UI 上：`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 持有 `public ManualExecutionGate Gate { get; } = new();` 并在 `ConfigureRun` 里赋值（赋值前先调 `Gate.Resume()`，这样一次运行绝不带着上一次留下的暂停开始）。每个完整版平台 demo 都把它接到暂停/恢复按钮上 —— 如 `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`、`Examples/Workflow/Avalonia/Demo/Views/Workflow/WorkflowView.axaml.cs`、`Examples/Workflow/Blazor/Demo/Demo/Components/Pages/Workflow.razor.cs` —— 并读 `Gate.IsPaused` 来显示「已暂停 / 空闲」。

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionGateTests.cs` —— `AClosedGate_HoldsTheRunAtTheNextNodeBoundary_AndResumeLetsItGo`、`AClosedGate_AlsoHoldsTheBranchesOfAFanOut`、`CancellingAPausedRun_EndsIt_InsteadOfWaitingForever`。

下一步见 `09_观察与报告`。
