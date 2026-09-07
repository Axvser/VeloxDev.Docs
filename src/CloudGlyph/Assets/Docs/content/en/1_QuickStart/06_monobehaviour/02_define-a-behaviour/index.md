# MonoBehaviour — Define a Behaviour

## 1. The attribute

A behaviour is any `partial` class annotated with `VeloxDev.TimeLine.MonoBehaviourAttribute`. The attribute takes two optional arguments (`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourAttribute.cs`):

- `channel` — the named channel the behaviour registers to. Default is the `"default"` channel (`MonoBehaviourManager.DEFAULT_CHANNEL`). All behaviours of a channel share the same two frame pumps.
- `fps` — the target FPS to request at registration time. `-1` (the default) means "leave the channel's existing setting alone"; a value of `1` or higher makes the generator call `MonoBehaviourManager.SetTargetFPS(fps, channel)` as part of registration.

The attribute is class-only, not inheritable and not repeatable.

```csharp
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
}
```

**Expected result:** the class compiles with no hand-written interface implementation — the generator turns it into an `IMonoBehaviour`.

## 2. What the generator emits

The generator (`Src/Generators/VeloxDev.Core.Generator/Writers/MonoWriter.cs`) synthesizes the other half of the class in the same namespace. The generated partial:

- implements `VeloxDev.MonoBehaviour.IMonoBehaviour`, so the class now has the bridge members `InitializeMonoBehaviour()`, `CloseMonoBehaviour()`, `InvokeAwake()`, `InvokeStart()`, `InvokeUpdate(FrameEventArgs)`, `InvokeLateUpdate(FrameEventArgs)` and `InvokeFixedUpdate(FrameEventArgs)`;
- declares the five **`partial void` lifecycle hooks** the loop calls through that bridge:

```csharp
partial void Awake();
partial void Start();
partial void Update(FrameEventArgs e);
partial void LateUpdate(FrameEventArgs e);
partial void FixedUpdate(FrameEventArgs e);
```

- adds `public void InitializeMonoBehaviour()` which registers the instance: it calls `MonoBehaviourManager.RegisterBehaviour(this, "game")` and, when `fps >= 1`, `MonoBehaviourManager.SetTargetFPS(fps, "game")` first;
- adds `public void CloseMonoBehaviour()` which calls `MonoBehaviourManager.UnregisterBehaviour(this, "game")`.

There is no `[Update]` attribute and no virtual `OnFrame` method to override: you implement the `partial void` hooks directly (with or without a body, matching the generated signature). A hook you do not implement is simply a no-op.

## 3. Register the instance

The generator never invents a constructor, so you must register each instance yourself — typically from your own constructor:

```csharp
public FrameCounter() => InitializeMonoBehaviour();
```

`InitializeMonoBehaviour()` only queues the registration on the channel. The hooks fire when a running channel drains its add-queue at the top of a frame:

- `Awake()` and `Start()` run once, the first time the behaviour is picked up by the loop;
- `Update(FrameEventArgs)` runs once per update frame;
- `LateUpdate(FrameEventArgs)` runs once per update frame, right after every behaviour's `Update`;
- `FixedUpdate(FrameEventArgs)` runs on the separate fixed-timestep pump (default every 16 ms).

**Expected result:** constructing `FrameCounter` registers it on the `"game"` channel; `Awake` / `Start` are not called yet because the channel is not running (see the [Configure & Run the Loop](../03_configure-and-run-the-loop/) page).

## 4. A complete minimal behaviour

```csharp
using System;
using System.Threading;
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
    public long UpdateCount;
    public long FixedUpdateCount;

    public FrameCounter() => InitializeMonoBehaviour();   // registers this instance on "game"

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
```

`Interlocked` keeps the counters correct because `Update` and `FixedUpdate` run on different loop threads. The class also illustrates that a nested-`Window`/base-class hierarchy is fine — the WPF demo annotates `MainWindow : Window` and nested `private partial class` components the same way (`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs`).

**Expected result:** this class plus a console host that calls `MonoBehaviourManager.Start("game")` prints the two bracketed lines exactly once each, and grows `UpdateCount` / `FixedUpdateCount` while the channel runs.

## Run declaration

- ⚠️ Statically verified only — the hook signatures and generated member shapes are transcribed from `MonoWriter.cs` and the `IMonoBehaviour` interface, and the counter behaviour pattern from the WPF demo; no compilation was run while writing this page. The whole program is compiled and run on the [Verify & Complete Code](../06_verify-and-complete-code/) page.
