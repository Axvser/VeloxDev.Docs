# MonoBehaviour — `IMonoBehaviour`

```csharp
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

| Member | Description |
|---|---|
| `InitializeMonoBehaviour()` | Registers the instance (`RegisterBehaviour(this, channel)`). Generated. |
| `CloseMonoBehaviour()` | Unregisters the instance (`UnregisterBehaviour(this, channel)`). Generated. |
| `InvokeAwake()` | Forwarded to the user `partial void Awake()`. |
| `InvokeStart()` | Forwarded to the user `partial void Start()`. |
| `InvokeUpdate(FrameEventArgs e)` | Forwarded to the user `partial void Update(FrameEventArgs e)`. |
| `InvokeLateUpdate(FrameEventArgs e)` | Forwarded to the user `partial void LateUpdate(FrameEventArgs e)`. |
| `InvokeFixedUpdate(FrameEventArgs e)` | Forwarded to the user `partial void FixedUpdate(FrameEventArgs e)`. |

**Notes:**
- The manager calls the `Invoke*` bridge; the bridge forwards to the partial hooks emitted by the generator (`MonoWriter.cs` lines 91-120). `Awake`/`Start` are invoked when the behaviour is added to the loop.
