# Start and Registration

The flow that turns `[Tickable]` on a class into "this object's `Awake` runs before the first frame". Two things make it non-obvious: the registration is **queued** rather than applied, and the drain happens **before** the frame is sampled.

```plantuml
@startuml
!theme plain

actor Caller as Caller
participant "Generated partial\n(user class)" as Gen
participant "TickManager\n(static facade)" as TM
participant "_channels\nConcurrentDictionary" as Dict
participant "LoopChannel\n(private engine)" as Ch
participant "ITimeSourceControl\n(the bus)" as Bus
participant "Update pump\n(thread)" as UT
participant "FixedUpdate pump\n(thread)" as FT

Caller -> Gen: InitializeTickable()
activate Gen

== Generated registration ==
Gen -> TM: SetTargetFPS(60, "demo")
note right of TM: emitted only when the attribute gave fps >= 1
TM -> Ch: GetOrCreateChannel("demo").SetTargetFPS(60)
Ch -> Ch: _configQueue.Enqueue(configRequest)

Gen -> TM: RegisterBehaviour(this, "demo")
activate TM
TM -> Ch: GetOrCreateChannel("demo")
activate Ch
Ch -> Dict: GetOrAdd("demo", factory)
alt first use of this channel name
    Dict -> Ch: new LoopChannel("demo")
    Ch -> Bus: TimerCore.CreateTimeSource<ITimeSourceControl>()
    Ch -> Ch: create _updateSampler / _fixedSampler
    Ch -> Ch: subscribe Started/Paused/Resumed/Stopped forwarders
else channel already exists
    Dict --> Ch: the existing instance
end
deactivate Ch
TM -> Ch: RegisterBehaviour(behavior)
Ch -> Ch: _addQueue.Enqueue(behavior)
deactivate TM
deactivate Gen

== Start ==
Caller -> TM: Start("demo")
activate TM
TM -> Ch: Start()
activate Ch
alt already running
    Ch --> TM: return - no events, no second pump
else not running
    Ch -> Ch: _isRunning = true; _cts = new CancellationTokenSource()
    Ch -> Ch: _updateSampler.Reset(); _fixedSampler.Reset()
    Ch -> Bus: Resume()
    note right of Bus: clears a pause left over from the previous lifecycle
    Ch -> Ch: RebuildCachedWrappers()
    Ch -> FT: new Thread(FixedUpdateLoop) - VeloxDev.FixedUpdate[demo]
    Ch -> UT: new Thread(UpdateLoop) - VeloxDev.Update[demo]
    Ch --> TM: Started
end
deactivate Ch
TM -> TM: OnChannelStarted?.Invoke(s, new TickChannelEventArgs("demo"))
deactivate TM

== Drain, before the first sample ==
UT -> Ch: ProcessMainThreadOperations()
activate Ch
Ch -> Ch: ProcessConfigChanges()
note right of Ch: applies the queued TargetFPS and the cached frame duration together
Ch -> Ch: ProcessAddedBehaviors()
Ch -> Ch: _wrapperPool.Get(); wrapper.Reset(behavior, ++_instanceCounter)
Ch -> Ch: _behaviors[RuntimeHelpers.GetHashCode(behavior)] = wrapper
Ch -> Ch: SafeExecute(behavior.InvokeAwake)
Ch -> Ch: SafeExecute(behavior.InvokeStart)
Ch -> Ch: _wrappersNeedSort = true
deactivate Ch

@enduml
```

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 276-330 (Start), 432-435 (RegisterBehaviour), 755-803 (the drain), 1019-1032 (GetOrCreateChannel), 1068-1069 (the static forward); `Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` lines 81-94.

## The ordering claim, stated precisely

The invariant is: **`Awake` and `Start` run before the first frame of that channel.**

The mechanism is not "register before start". It is that `ProcessMainThreadOperations` — which includes `ProcessAddedBehaviors` — is called at the top of the update loop body, *before* `_updateSampler.Sample()`:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 530-541)
var frameStartTime = GetTimestamp();
ProcessMainThreadOperations();

// 无偿采样：总线没前进就没有帧可推。
var sample = _updateSampler.Sample();
if (sample.Delta == TimeSpan.Zero)
{
    Sleep(TimeSpan.FromMilliseconds(MIN_SLEEP_MS), token);
    continue;
}

var frameArgs = CreateFrameEventArgs(sample.Delta, sample.Total);
```

So both orderings hold:

| Caller order | What happens |
|---|---|
| `InitializeTickable()` then `Start(name)` | The queue is drained on the first iteration, before the first sample. `Awake` → `Start` → first `Update`. |
| `Start(name)` then `InitializeTickable()` | The queue is drained on the next iteration, before that frame's sample. Still `Awake` → `Start` → `Update`. |

The WPF demo relies on and measures this: `MainWindow.xaml.cs` registers, sets the frame rate, then starts (lines 57-61), and `SimState.AwakeAtUpdateCount` records the `Update` counter at the moment `Awake` ran — it is zero, which is the evidence rather than the claim.

## `Awake` / `Start` versus stopping and restarting

The table that catches people out, with the mechanism behind each row:

| Action | Lifecycle re-runs? | Why |
|---|---|---|
| `StopAsync` + `Start` | No | `StopAsync` clears the *queues* (`ClearQueues`, line 956) and resets the statistics; the behaviour dictionary survives, so the surviving registrations tick again after `Start` without re-running `Awake` / `Start`. Only a registration still queued at the stop is lost. |
| `RestartAsync` | No | Same — it is `StopAsync` + waits + `Start`. |
| `CloseTickable()` + `InitializeTickable()` | **Yes** | A fresh wrapper is drawn from `_wrapperPool` and `InvokeAwake` / `InvokeStart` run on it. |

Note the asymmetry: stopping a channel does not tell the behaviour (there is no "closed" hook on `ITickable`) and does not remove applied registrations; re-registering an instance that is still registered replaces the wrapper and re-runs both hooks. `MainWindow.xaml.cs` lines 105-119 exposes both pairs of buttons so the distinction is visible rather than asserted.

## Failure and edge paths

- **`null` behaviour.** `RegisterBehaviour` filters it (`if (behavior != null)`, line 432), so the queue never sees one. A `null` that somehow arrives is skipped again by the drain (`if (behavior == null) continue;`, line 790).
- **Duplicate registration.** `_behaviors` is keyed by `RuntimeHelpers.GetHashCode(behavior)`, so the second registration overwrites the first wrapper. `Awake` and `Start` still run again — on the new wrapper.
- **`Start` on a running channel.** Returns at line 276: no new threads, no second `OnChannelStarted`.
- **Registering on a channel that was never started.** The entry sits in `_addQueue` until someone calls `Start`. It is not lost, and it is not started.
- **A throwing `Awake` / `Start`.** `SafeExecute` catches it and writes to `Debug.WriteLine`; `InvokeStart` still runs, and the drain still sets `_wrappersNeedSort`.
- **Registering during `StopAsync`.** The queues are cleared in the `finally` block, so a registration still queued when the stop completes is dropped. Re-register after the stop completes. A registration applied before the stop stays registered.
