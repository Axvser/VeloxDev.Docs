# `ITickable`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public interface ITickable
{
    void InitializeTickable();
    void CloseTickable();
    void InvokeAwake();
    void InvokeStart();
    void InvokeUpdate(FrameEventArgs e);
    void InvokeLateUpdate(FrameEventArgs e);
    void InvokeFixedUpdate(FrameEventArgs e);
}
```

Source: `Src/Core/VeloxDev.Core/Interfaces/Tickable/ITickable.cs`.

This is the interface formerly named `IMonoBehaviour`, and the namespace it lives in is now `VeloxDev.TimeLine` rather than `VeloxDev.MonoBehaviour` — so the old `using VeloxDev.MonoBehaviour;` no longer compiles. The member names `InitializeTickable` / `CloseTickable` are also new (`InitializeMonoBehaviour` / `CloseMonoBehaviour`).

**You almost never implement this by hand.** The source generator writes all seven members for any `partial` class carrying `[Tickable]`, and `TickManager.RegisterBehaviour` takes the interface only because that is the shape the channel dispatches through. Implementing it manually is legal and is what the tests do when they want a minimal behaviour.

| Member | Called by | Typical body |
|---|---|---|
| `InitializeTickable()` | you | `TickManager.RegisterBehaviour(this, "<channel>")` — the generated version also calls `SetTargetFPS` when the attribute gave an `fps` |
| `CloseTickable()` | you | `TickManager.UnregisterBehaviour(this, "<channel>")` |
| `InvokeAwake()` | the update pump's registration drain | call your `Awake` |
| `InvokeStart()` | the same drain, immediately after `InvokeAwake()` | call your `Start` |
| `InvokeUpdate(FrameEventArgs)` | the update pump, once per frame | call your `Update` |
| `InvokeLateUpdate(FrameEventArgs)` | the update pump, once per frame, after every behaviour's `InvokeUpdate` | call your `LateUpdate` |
| `InvokeFixedUpdate(FrameEventArgs)` | the fixed-update pump, once per owed step | call your `FixedUpdate` |

#### `ITickable.InitializeTickable`

**Signature:**
`void InitializeTickable()`

**Returns:** `void`.

**Notes:**
- **The loop never calls this.** It is the user's entry point into registration, not a framework callback; the generated implementation is the one place that knows the channel name.
- The channel it registers on comes from the `[Tickable]` attribute's `Channel`, baked in as a string literal at compile time — an instance carries no channel of its own.

#### `ITickable.CloseTickable`

**Signature:**
`void CloseTickable()`

**Returns:** `void`.

**Notes:**
- Also never called by the loop. Unregistration is silent: the pump simply stops dispatching, and there is no "closed" hook on the behaviour.
- After `CloseTickable()`, the instance is still usable and can be registered again — which re-runs `InvokeAwake` and `InvokeStart` on a fresh wrapper.

#### `ITickable.InvokeAwake`

**Signature:**
`void InvokeAwake()`

**Returns:** `void`.

**Notes:**
- Called once per registration, during the update pump's registration drain (`ProcessAddedBehaviors`, `TickManager.cs` lines 785-801), **before the first frame body**.
- Wrapped in `SafeExecute` (lines 939-942), so an exception here is logged to `Debug.WriteLine` and does not prevent `InvokeStart` or the loop from running.
- Called on the update thread, not the caller's thread: `RegisterBehaviour` only enqueues.

#### `ITickable.InvokeStart`

**Signature:**
`void InvokeStart()`

**Returns:** `void`.

**Notes:**
- Called immediately after `InvokeAwake` in the same drain, in the same frame.
- Same `SafeExecute` guard, same thread.

#### `ITickable.InvokeUpdate`

**Signature:**
`void InvokeUpdate(FrameEventArgs e)`

| Parameter | Type | Description |
|---|---|---|
| `e` | `FrameEventArgs` | The frame's pooled arguments. `e.Handled` is `false` when the call is made; setting it stops the rest of this frame phase. |

**Returns:** `void`.

**Notes:**
- One call per frame per registered behaviour, on the channel's update thread, in registration order.
- The dispatch loop checks `frameArgs.Handled` and the cancellation token **before** each behaviour (`ExecuteBehaviorsUpdateSync`, lines 689-702), so a behaviour that sets `Handled` is not skipped — everything after it is.
- Exceptions are caught per behaviour and written to `Debug.WriteLine`; the loop continues with the next behaviour.

#### `ITickable.InvokeLateUpdate`

**Signature:**
`void InvokeLateUpdate(FrameEventArgs e)`

**Returns:** `void`.

**Notes:**
- A separate loop over the same business array with its own `Handled` check, which is why setting `Handled` in `InvokeUpdate` skips the **entire** late phase for the frame rather than just this behaviour's late callback.
- Runs on the update thread, after every behaviour's `InvokeUpdate` for that frame.

#### `ITickable.InvokeFixedUpdate`

**Signature:**
`void InvokeFixedUpdate(FrameEventArgs e)`

**Returns:** `void`.

**Notes:**
- Runs on the fixed-update thread, **concurrently** with `InvokeUpdate` / `InvokeLateUpdate`. Any field both touch needs its own synchronisation.
- Each owed step gets its own `FrameEventArgs`, built per step and returned to the pool immediately (`FixedUpdateLoop`, lines 483-493), so a `Handled` flag set in `InvokeUpdate` never reaches this pump.
- A stall is repaid as several calls in a row, up to the sampler's per-call cap.

## Implementing it by hand

`Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` lines 45-67 — the smallest legal implementation, used by the tests when no generator is in play:

```csharp
private sealed class PushCounter : ITickable
{
    private int _updates;
    private int _fixedUpdates;

    public int Updates => Volatile.Read(ref _updates);

    public int FixedUpdates => Volatile.Read(ref _fixedUpdates);

    public void InitializeTickable() { }

    public void CloseTickable() { }

    public void InvokeAwake() { }

    public void InvokeStart() { }

    public void InvokeUpdate(FrameEventArgs e) => Interlocked.Increment(ref _updates);

    public void InvokeLateUpdate(FrameEventArgs e) { }

    public void InvokeFixedUpdate(FrameEventArgs e) => Interlocked.Increment(ref _fixedUpdates);
}
```

Note what the test does with it — `InitializeTickable()` is left empty and registration goes through `TickManager.RegisterBehaviour(counter, channel)` directly. That is the honest division: `InitializeTickable` exists only so a generated class has somewhere to put a channel name.
