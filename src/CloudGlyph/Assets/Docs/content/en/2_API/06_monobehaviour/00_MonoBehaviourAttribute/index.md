# MonoBehaviour — `MonoBehaviourAttribute`

`[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]`

```csharp
public sealed class MonoBehaviourAttribute(string channel = MonoBehaviourManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; }
    public int TargetFPS { get; set; }
}
```

Marks a `partial` class as a frame-driven behaviour. The source generator reads this attribute and emits the `IMonoBehaviour` bridge (`MonoWriter.cs` lines 13-50, 80-121).

#### `MonoBehaviourAttribute.MonoBehaviourAttribute` (constructor)

**Signature:**
`public MonoBehaviourAttribute(string channel = MonoBehaviourManager.DEFAULT_CHANNEL, int fps = -1)`

| Parameter | Type | Description |
|---|---|---|
| `channel` | `string` | The named loop channel the behaviour registers to. Defaults to `"default"`. |
| `fps` | `int` | Target FPS applied on registration; `-1` leaves the channel's existing setting unchanged. |

**Returns:** `MonoBehaviourAttribute`

**Example:**
```text
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (line 8)
[MonoBehaviour]
public partial class MainWindow : Window { ... }
```

**Notes:**
- Valid on classes only, not inherited, not repeatable (verified by `MonoBehaviourAttributeTests.AttributeUsage_ClassOnly`).

#### `MonoBehaviourAttribute.Channel`

**Signature:**
`public string Channel { get; }`

**Returns:** `string` — the named channel the behaviour targets.

**Notes:**
- Read-only; the generator uses it to emit `RegisterBehaviour(this, "channel")` (`MonoWriter.cs` lines 76-84).

#### `MonoBehaviourAttribute.TargetFPS`

**Signature:**
`public int TargetFPS { get; set; }`

**Returns:** `int` — `-1` means "keep the channel setting"; any value `>= 1` is applied via `MonoBehaviourManager.SetTargetFPS` before registration.

**Notes:**
- Settable via named argument: `[MonoBehaviour(channel: "game", fps: 60)]`.
