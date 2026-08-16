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

| 成员 | 说明 |
|---|---|
| `InitializeMonoBehaviour()` | 注册实例（`RegisterBehaviour(this, channel)`）。由生成器生成。 |
| `CloseMonoBehaviour()` | 注销实例（`UnregisterBehaviour(this, channel)`）。由生成器生成。 |
| `InvokeAwake()` | 转发到用户 `partial void Awake()`。 |
| `InvokeStart()` | 转发到用户 `partial void Start()`。 |
| `InvokeUpdate(FrameEventArgs e)` | 转发到用户 `partial void Update(FrameEventArgs e)`。 |
| `InvokeLateUpdate(FrameEventArgs e)` | 转发到用户 `partial void LateUpdate(FrameEventArgs e)`。 |
| `InvokeFixedUpdate(FrameEventArgs e)` | 转发到用户 `partial void FixedUpdate(FrameEventArgs e)`。 |

**说明：**
- 管理器调用 `Invoke*` 桥接；桥接再转发到生成器产出的 partial 钩子（`MonoWriter.cs` 第 91-120 行）。行为加入循环时调用 `Awake` / `Start`。
