# MonoBehaviour — `IMonoBehaviour`

Namespace `VeloxDev.MonoBehaviour`. The behaviour contract the source generator (`VeloxDev.Core.Generator`) implements for every class decorated with `[MonoBehaviour]`.

```csharp
namespace VeloxDev.MonoBehaviour;

public interface IMonoBehaviour
{
    void InitializeMonoBehaviour();
    void CloseMonoBehaviour();
    void InvokeAwake();
    void InvokeStart();
    void InvokeUpdate(FrameEventArgs e);
    void InvokeLateUpdate(FrameEventArgs e);
    void InvokeFixedUpdate(FrameEventArgs e);
}
```

| Member | Invoked by | Generated body |
|---|---|---|
| `InitializeMonoBehaviour()` | User code (e.g. the class constructor) | Registers the instance: `MonoBehaviourManager.RegisterBehaviour(this, channel)`. |
| `CloseMonoBehaviour()` | User code | Unregisters the instance: `MonoBehaviourManager.UnregisterBehaviour(this, channel)`. |
| `InvokeAwake()` | `MonoBehaviourManager` when the behaviour is added | Forwards to the user `partial void Awake()`. |
| `InvokeStart()` | `MonoBehaviourManager` when the behaviour is added | Forwards to the user `partial void Start()`. |
| `InvokeUpdate(FrameEventArgs e)` | `MonoBehaviourManager` every frame | Forwards to the user `partial void Update(FrameEventArgs e)`. |
| `InvokeLateUpdate(FrameEventArgs e)` | `MonoBehaviourManager` every frame | Forwards to the user `partial void LateUpdate(FrameEventArgs e)`. |
| `InvokeFixedUpdate(FrameEventArgs e)` | `MonoBehaviourManager` every fixed interval | Forwards to the user `partial void FixedUpdate(FrameEventArgs e)`. |

**Notes:**

- The manager never calls `InitializeMonoBehaviour()` / `CloseMonoBehaviour()`; they are invoked by user code. The demo pattern calls `InitializeMonoBehaviour()` from the constructor to register, and the generated `CloseMonoBehaviour()` to unregister.
- The generator emits the implementation and the empty `partial void` hooks in one partial class; the class only supplies the method bodies. See `Src/Generators/VeloxDev.Core.Generator/Writers/MonoWriter.cs`.

**Source:**

`Src/Core/VeloxDev.Core/Interfaces/MonoBehaviour/`
