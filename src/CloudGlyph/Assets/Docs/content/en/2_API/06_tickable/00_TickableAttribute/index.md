# `TickableAttribute`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TickableAttribute.cs`.

Two usages of the attribute are rejected by the runtime rather than by the compiler's attribute rules, so they are worth stating explicitly: it applies to **classes only** (not to members, structs, records-as-classes being the exception — a `record class` is a class and is accepted), and it is **not inherited**, so `[Tickable]` on a base type does not put a derived type on any channel.

### Constructor

#### `TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1)`

**Signature:**
`public TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1)`

| Parameter | Type | Description |
|---|---|---|
| `channel` | `string` | The named channel the generated `InitializeTickable()` registers on. Defaults to `TickManager.DEFAULT_CHANNEL` (`"default"`). |
| `fps` | `int` | Target FPS for that channel. `-1` (the default) emits no FPS call at all; any value `>= 1` makes the generated registration call `TickManager.SetTargetFPS(fps, channel)` first. Values `<= 0` other than `-1` are treated the same as `-1` by the generator's `TargetFPS >= 1` test. |

**Returns:** a new attribute instance. The `channel` argument is stored in the read-only `Channel` property; the `fps` argument is stored in the settable `TargetFPS` property.

**Exceptions:** none.

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs (line 30)
[Tickable(DemoChannel.Name)]
public partial class MainWindow

// DemoChannel.Name is TickManager.DEFAULT_CHANNEL, and fps is left at -1,
// so the window's own SetTargetFPS(30, ...) call is not overwritten.
```

**Notes:**
- The generator reads the attribute by symbol, not by name, so a fully qualified or aliased form works too (`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` lines 19-27).
- The generator resolves **named** arguments after positional ones, so `[Tickable(Channel = "x")]` and `[Tickable("x")]` are equivalent, and a named argument wins over a positional one (`TickWriter.cs` lines 39-48).
- `TargetFPS <= 0` is not clamped by the attribute — the *generator* simply declines to emit the call.

#### Property: `TickableAttribute.Channel`

**Signature:**
`public string Channel { get; }`

**Returns:** `string` — the channel name the behaviour is registered on. Never `null`; the constructor's default supplies `TickManager.DEFAULT_CHANNEL` when the caller passes nothing.

**Notes:**
- Get-only. There is no way to change a behaviour's channel after construction, and the generator bakes the channel name into the generated `InitializeTickable()` / `CloseTickable()` as a string literal at compile time.
- The generated code passes this string to `TickManager.RegisterBehaviour(this, "<channel>")`, which is the same call you would make by hand.

#### Property: `TickableAttribute.TargetFPS`

**Signature:**
`public int TargetFPS { get; set; }`

**Returns:** `int` — the target frames per second to apply when this behaviour registers. `-1` means "do not touch the channel's FPS".

**Notes:**
- Unlike `Channel`, this one is settable, so the named-argument form `[Tickable(TargetFPS = 60)]` works.
- The value is a **target for the channel**, not a per-behaviour rate. Two behaviours on the same channel that declare different `TargetFPS` values will overwrite each other at registration time, in registration order.

### Attribute usage, verified

`Src/Core/VeloxDev.Core.Test/TimeLine/TickableAttributeTests.cs`:

```csharp
[TestMethod]
public void AttributeUsage_ClassOnly()
{
    var usage = (AttributeUsageAttribute?)Attribute.GetCustomAttribute(
        typeof(TickableAttribute), typeof(AttributeUsageAttribute));
    Assert.IsNotNull(usage);
    Assert.AreEqual(AttributeTargets.Class, usage.ValidOn);
    Assert.IsFalse(usage.AllowMultiple);
    Assert.IsFalse(usage.Inherited);
}
```
