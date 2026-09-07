# MonoBehaviour — `IMonoBehaviour`

命名空间 `VeloxDev.MonoBehaviour`。源生成器（`VeloxDev.Core.Generator`）为每个以 `[MonoBehaviour]` 标记的类实现的行为契约。

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

| 成员 | 由谁调用 | 生成的实现 |
|---|---|---|
| `InitializeMonoBehaviour()` | 用户代码（如类构造函数） | 注册实例：`MonoBehaviourManager.RegisterBehaviour(this, channel)`。 |
| `CloseMonoBehaviour()` | 用户代码 | 注销实例：`MonoBehaviourManager.UnregisterBehaviour(this, channel)`。 |
| `InvokeAwake()` | `MonoBehaviourManager`（行为加入时） | 转发到用户 `partial void Awake()`。 |
| `InvokeStart()` | `MonoBehaviourManager`（行为加入时） | 转发到用户 `partial void Start()`。 |
| `InvokeUpdate(FrameEventArgs e)` | `MonoBehaviourManager`（每帧） | 转发到用户 `partial void Update(FrameEventArgs e)`。 |
| `InvokeLateUpdate(FrameEventArgs e)` | `MonoBehaviourManager`（每帧） | 转发到用户 `partial void LateUpdate(FrameEventArgs e)`。 |
| `InvokeFixedUpdate(FrameEventArgs e)` | `MonoBehaviourManager`（每个固定间隔） | 转发到用户 `partial void FixedUpdate(FrameEventArgs e)`。 |

**说明：**

- 管理器从不调用 `InitializeMonoBehaviour()` / `CloseMonoBehaviour()`；它们由用户调用——示例中的模式是在构造函数里调用 `InitializeMonoBehaviour()` 完成注册，需要注销时调用生成的 `CloseMonoBehaviour()`。
- 生成器在一个 partial 类中同时产出实现与空的 `partial void` 钩子；用户类只需提供方法体。参见 `Src/Generators/VeloxDev.Core.Generator/Writers/MonoWriter.cs`。

**源码：**

`Src/Core/VeloxDev.Core/Interfaces/MonoBehaviour/`
