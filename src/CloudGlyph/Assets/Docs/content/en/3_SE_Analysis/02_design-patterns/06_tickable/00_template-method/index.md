# Template Method — the frame loop

The loop skeleton is fixed inside the private `LoopChannel`; the variable steps are the user's five `partial void` hooks. The source generator is the bridge between the two, and it is the reason the user never subclasses anything.

| Role | Element | Source |
|---|---|---|
| Skeleton (thread path) | `LoopChannel.UpdateLoop` | `TickManager.cs` 509-554 |
| Skeleton (thread path) | `LoopChannel.FixedUpdateLoop` | `TickManager.cs` 446-507 |
| Skeleton (async path) | `UpdateLoopAsync` / `FixedUpdateLoopAsync` | `TickManager.cs` 622-682 / 557-620 |
| Per-behaviour execution | `ExecuteBehaviorsUpdateSync` / `…LateUpdateSync` / `…FixedUpdateSync` | `TickManager.cs` 689-734 |
| Hook methods | `partial void Awake` / `Start` / `Update` / `LateUpdate` / `FixedUpdate` | `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs` 52-168 |
| Bridge | the generated `Invoke*` methods | `Writers/TickWriter.cs` 80-121 |
| Registration entry points | the generated `InitializeTickable()` / `CloseTickable()` | `Writers/TickWriter.cs` 81-89 |

## The skeleton

`UpdateLoop` is the invariant algorithm. Everything in it is fixed except the three lines that dispatch into user code:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 509-554, abridged to the shape)
private void UpdateLoop(CancellationToken token)
{
    _isUpdateThreadActive = true;
    Interlocked.Exchange(ref _updateThreadLastActivityTimestamp, GetTimestamp());

    try
    {
        while (_isRunning && !token.IsCancellationRequested)
        {
            Interlocked.Exchange(ref _updateThreadLastActivityTimestamp, GetTimestamp());

            if (!_bus.IsAdvancing)
            {
                _bus.WaitWhileStalledAsync(token).GetAwaiter().GetResult();
                continue;
            }

            var frameStartTime = GetTimestamp();
            ProcessMainThreadOperations();

            var sample = _updateSampler.Sample();
            if (sample.Delta == TimeSpan.Zero)
            {
                Sleep(TimeSpan.FromMilliseconds(MIN_SLEEP_MS), token);
                continue;
            }

            var frameArgs = CreateFrameEventArgs(sample.Delta, sample.Total);

            ExecuteBehaviorsUpdateSync(frameArgs, token);
            ExecuteBehaviorsLateUpdateSync(frameArgs, token);

            _frameEventArgsPool.Return(frameArgs);

            UpdatePerformanceStats(frameStartTime, sample.Total);
            FrameRateControlSync(frameStartTime, token);
            Interlocked.Increment(ref _totalFrames);
        }
    }
    catch (OperationCanceledException) { }
    finally
    {
        _isUpdateThreadActive = false;
    }
}
```

The fixed parts, in order: activity timestamp → stall check → main-thread drain → sample → build args → dispatch Update → dispatch LateUpdate → return the args to the pool → publish stats → pace → count the frame. A subclass-based design would put `ExecuteBehaviors*` behind `protected virtual` methods; here they are private and the extension point is the *behaviour*, not the loop. There is nothing to subclass because `LoopChannel` is `private sealed` — the only way in is `ITickable`.

`FixedUpdateLoop` is a different skeleton with the same spirit: apply a pending step-size change on its own thread, stall-check, `Advance` the compensating sampler, then push `count` steps in a loop, each building and returning its own args (lines 457-499).

## The bridge

The generator writes the only code that knows both halves. `TickWriter.GenerateBody` (lines 69-122) emits, into a partial declaration of the user's class:

```csharp
public void InitializeTickable()
{
    global::VeloxDev.TimeLine.TickManager.SetTargetFPS(60, "demo");
    global::VeloxDev.TimeLine.TickManager.RegisterBehaviour(this, "demo");
}

public void CloseTickable()
{
    global::VeloxDev.TimeLine.TickManager.UnregisterBehaviour(this, "demo");
}

public void InvokeAwake()        { Awake(); }
public void InvokeStart()        { Start(); }
public void InvokeUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)      { Update(e); }
public void InvokeLateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)  { LateUpdate(e); }
public void InvokeFixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e) { FixedUpdate(e); }

partial void Awake();
partial void Start();
partial void Update(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void LateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void FixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
```

Two properties of this generated code matter:

- **The `SetTargetFPS` line is conditional.** `TickWriter` builds it only when the resolved attribute FPS is `>= 1` (`var setFpsLine = TargetFPS >= 1 ? … : string.Empty;`, line 76). With `[Tickable("demo")]` no FPS call is emitted at all, so registration cannot silently overwrite a channel setting.
- **The `partial void` declarations are what make the hooks optional.** A hook the user does not write is removed by the compiler, with no empty override and no virtual call. This is the Template Method with a *zero-cost* absent step, which is not something a `virtual`-based template can offer.

## The lifecycle steps

Registration is deferred, and that is the part of the template that is easiest to misread. `RegisterBehaviour` enqueues; the drain happens at the top of the frame, before the sample:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 785-801)
private void ProcessAddedBehaviors()
{
    bool added = false;
    while (_addQueue.TryDequeue(out var behavior))
    {
        if (behavior == null) continue;

        var wrapper = _wrapperPool.Get();
        wrapper.Reset(behavior, Interlocked.Increment(ref _instanceCounter));

        _behaviors[RuntimeHelpers.GetHashCode(behavior)] = wrapper;
        SafeExecute(behavior.InvokeAwake);
        SafeExecute(behavior.InvokeStart);
        added = true;
    }
    if (added) _wrappersNeedSort = true;
}
```

`ProcessMainThreadOperations` (line 753) calls this before `_updateSampler.Sample()`, so `Awake` and `Start` always precede the first `Update` — whether registration happened before or after `Start`. The WPF demo turns this into a visible measurement rather than a claim: `SimState.AwakeAtUpdateCount` and `AwakeFrameOrdinal` record the `Update` counter and the engine frame ordinal at the moment `Awake` ran.

| Hook | Driver | Frequency |
|---|---|---|
| `Awake` | update pump, registration drain | Once per registration |
| `Start` | update pump, immediately after `Awake` | Once per registration |
| `Update` | update pump | Every frame |
| `LateUpdate` | update pump | Every frame, after every behaviour's `Update` — unless `Handled` was raised |
| `FixedUpdate` | fixed-update pump | Every step interval (default 16 ms), concurrently, in batches after a stall |

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 446-554, 689-734, 753-801; `Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` lines 64-125.
