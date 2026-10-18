# 工作流系统 — 暂停并恢复运行

一次编译运行是一长串 await 的节点驱动。`ManualExecutionGate` 是暂停点：引擎在驱动每个节点前 await 它，因此宿主可以在节点边界停住运行，再放行。在 `WorkflowQuickStart` 工程中按「安装与创建项目」创建相关代码。

## 1. 把闸门挂到会话上

闸门属于会话，而不是引擎：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var gate = new ManualExecutionGate();
var context = new RuntimeContext { ExecutionGate = gate };
```

**预期结果：** 代码可编译，`gate.IsPaused` 为 `false`。

## 2. 停住运行

在开始运行**之前**调用 `Pause()` —— 引擎到达的第一个节点边界会阻塞：

```csharp
gate.Pause();
var run = new RuntimeEngine().RunAsync(rootGraph, context, CancellationToken.None);
await Task.Delay(80);          // let the engine reach the first boundary
```

**预期结果：** `context.Status == "Paused"`、`gate.IsPaused == true`、`context.IsRunning == true`，且 `context.Data` 仍为 `null` —— 还没有节点被驱动。注意第三项：**暂停不是停止**，运行仍在进行中。

## 3. 放行

```csharp
gate.Resume();
await run;

Console.WriteLine($"{context.Status} {context.Data}");
```

**预期结果：** 运行正常完成 —— `Completed tick->bias->print`。闸门释放的瞬间 `Status` 回到 `"Running"`，随后变为 `"Completed"`。

## 4. 从另一个线程暂停

宿主在其 UI 线程暂停，而运行停在调度器上；`Pause` 与 `Resume` 可从任何线程安全调用，包括驱动运行的那个线程：

```csharp
// Exposed by the demo session as a bindable property:
public ManualExecutionGate Gate { get; } = new();

Gate.Pause();     // holds at the next node boundary
Gate.Resume();    // lets it go
```

**预期结果：** 暂停在下一个节点边界生效，绝不会在节点中途 —— 已被驱动的节点总是跑完。

## 5. 停止一个暂停中的运行

在运行被停住时取消它的令牌，会结束它而不是挂起：

```csharp
var cts = new CancellationTokenSource();
var held = new RuntimeEngine().RunAsync(rootGraph, context, cts.Token);
gate.Pause();
await Task.Delay(50);
cts.Cancel();
await held;                                   // returns; it does not hang

Console.WriteLine($"{context.Status} {context.Outcome}");
```

**预期结果：** `Stopped Cancelled`。这就是 `IExecutionGate.WaitAsync` 在取消时必须**抛异常**而不是返回的原因：若调用方在闸门未打开时正常返回，它就会继续驱动。

## 6. 真实仓库中的位置

demo 把同一个闸门接到宿主 UI：`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 拥有 `public ManualExecutionGate Gate { get; } = new();`，并在 `ConfigureRun` 中赋值（在 `Gate.Resume()` 之后，确保一次运行不会一开始就卡在上一轮的暂停上）。每个完整平台 demo 都把暂停/恢复按钮绑定到它 —— 例如 `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`、`Examples/Workflow/Avalonia/Demo/Views/Workflow/WorkflowView.axaml.cs`、`Examples/Workflow/Blazor/Demo/Demo/Components/Pages/Workflow.razor.cs` —— 并读取 `Gate.IsPaused` 显示暂停/空闲状态。

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionGateTests.cs` —— `AClosedGate_HoldsTheRunAtTheNextNodeBoundary_AndResumeLetsItGo`、`AClosedGate_AlsoHoldsTheBranchesOfAFanOut`、`CancellingAPausedRun_EndsIt_InsteadOfWaitingForever`。

前往「观察与报告」。
