# Workflow System — Pause and Resume a Run

A compiled run is a long sequence of awaited node drives. `ManualExecutionGate` is the pause point: the engine awaits it before driving each node, so a host can hold the run at a node boundary and let it go again. Create the class in the `WorkflowQuickStart` project from `Install & Create the Project`.

## 1. Attach a gate to the session

The gate lives on the session, not on the engine:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var gate = new ManualExecutionGate();
var context = new RuntimeContext { ExecutionGate = gate };
```

**Expected result:** the session compiles and `gate.IsPaused` is `false`.

## 2. Hold the run

Call `Pause()` before starting the run — the first node boundary the engine reaches will block:

```csharp
gate.Pause();
var run = new RuntimeEngine().RunAsync(rootGraph, context, CancellationToken.None);
await Task.Delay(80);          // let the engine reach the first boundary
```

**Expected result:** `context.Status == "Paused"`, `gate.IsPaused == true`, `context.IsRunning == true`, and `context.Data` is still `null` — no node has been driven. Note the third one: **paused is not stopped**, the run is still in flight.

## 3. Let it go

```csharp
gate.Resume();
await run;

Console.WriteLine($"{context.Status} {context.Data}");
```

**Expected result:** the run completes normally — `Completed tick->bias->print`. `Status` goes back to `"Running"` the moment the gate is released and then to `"Completed"`.

## 4. Pausing mid-run from another source

A host pauses from its UI thread while the run is parked on the dispatcher; both `Pause` and `Resume` are safe from any thread, including the one driving:

```csharp
// Exposed by the demo session as a bindable property:
public ManualExecutionGate Gate { get; } = new();

Gate.Pause();     // holds at the next node boundary
Gate.Resume();    // lets it go
```

**Expected result:** the pause takes effect at the next node boundary, never mid-node — a node already being driven always runs to completion.

## 5. Stopping a paused run

Cancelling the run's token while it is held ends it rather than hanging:

```csharp
var cts = new CancellationTokenSource();
var held = new RuntimeEngine().RunAsync(rootGraph, context, cts.Token);
gate.Pause();
await Task.Delay(50);
cts.Cancel();
await held;                                   // returns; it does not hang

Console.WriteLine($"{context.Status} {context.Outcome}");
```

**Expected result:** `Stopped Cancelled`. This is why `IExecutionGate.WaitAsync` must **throw** on cancellation rather than return: a caller that came back without the gate being opened would keep driving.

## 6. Where this lives in the real repository

The demo wires the same gate to host UI: `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` owns `public ManualExecutionGate Gate { get; } = new();` and assigns it in `ConfigureRun` (after calling `Gate.Resume()`, so one run never starts holding the last run's pause). Every full platform demo binds Pause / Resume buttons to it — e.g. `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, `Examples/Workflow/Avalonia/Demo/Views/Workflow/WorkflowView.axaml.cs`, `Examples/Workflow/Blazor/Demo/Demo/Components/Pages/Workflow.razor.cs`, and reads `Gate.IsPaused` to show a paused/idle state.

Tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionGateTests.cs` — `AClosedGate_HoldsTheRunAtTheNextNodeBoundary_AndResumeLetsItGo`, `AClosedGate_AlsoHoldsTheBranchesOfAFanOut`, `CancellingAPausedRun_EndsIt_InsteadOfWaitingForever`.

Go to `Observe and report`.
