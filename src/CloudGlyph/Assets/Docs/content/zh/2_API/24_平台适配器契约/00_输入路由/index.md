# WorkflowInput 与输入中继

`WorkflowInput` 是一棵树唯一的输入路由。适配器把平台的指针或键盘输入翻译成标准参数类型并调用 `Route`；路由把同一个参数实例依次交给目标、目标的祖先、最后是树。`IInputEvents` 是可选的 Helper 能力，携带该组件的中继。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## WorkflowInput

**签名：** `sealed class WorkflowInput`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowInput(ITreeComponent tree)` | 构造函数 | 创建路由；`tree` 为 null 时抛 `ArgumentNullException`。 |
| `For(ITreeComponent tree)` | `static WorkflowInput` | 返回 `tree` 唯一的路由，首次使用时创建，并由 `ConditionalWeakTable` 持有。 |
| `Tree` | `ITreeComponent` | 该路由所属的树。 |
| `PointerTarget` | `IWorkflowComponent?` | 指针所在的组件；空白画布上为 `null`。除非设置了 `IsSuspended`，否则由路由维护。 |
| `HoveredLink` | `ILinkComponent?` | `PointerTarget` 作为连线的形式，或 `null`。 |
| `ConnectionSender` | `ISlotComponent?` | 连接拖拽的起点端口。 |
| `PreviewReceiver` | `ISlotComponent?` | 拖拽期间指针下的候选端口。 |
| `PreviewState` | `ConnectionPreviewState` | 连接拖拽的当前阶段。 |
| `PreviewCheck` | `ConnectionCheck?` | 候选端口的检查结果；非法候选同样带检查。 |
| `PreviewChanged` | `event EventHandler<ConnectionPreviewEventArgs>` | 起点、候选或阶段变化时触发。 |
| `PreviewValidating` | `event EventHandler<ConnectionPreviewValidatingEventArgs>` | 对框架认为合法的候选触发一次；订阅者可仅对本次预览拒绝它。 |
| `HitRadius` | `double` | 连线两侧的命中范围；默认 `LinkHitTestEx.DefaultHitRadius`（6）。 |
| `IsSuspended` | `bool` | 阻止指针移动更新 `PointerTarget`，用于宿主弹出层。 |
| `Scroller` | `IWorkflowSurfaceScroller?` | 由挂载中的适配器注册；摘除后为 `null`。 |
| `Navigator` | `IWorkflowSurfaceNavigator?` | 由挂载中的适配器注册；摘除后为 `null`。 |
| `Route(PointerEventArgs e)` | `void` | 把指针事件交给目标及祖先，然后执行框架自身的反应。 |
| `Route(KeyEventArgs e)` | `void` | 分发键盘事件；Core 没有默认键盘动作。 |

两个 `Route` 重载在参数为 null 时都抛 `ArgumentNullException`。

### 分发顺序

`Route(PointerEventArgs)` 依次做三件事：

1. 若指针更换了组件，先向旧组件冒泡一个 `PointerExitedEventArgs`，再向新组件冒泡一个 `PointerEnteredEventArgs`。它们是两个独立动作，各自持有自己的 `WorkflowEventHandle`。
2. 把参数沿 `目标 → 目标所属节点（插槽时）→ 树` 冒泡。
3. 若未设置 `PreventDefault`，记录新的 `PointerTarget`（除非 `IsSuspended`）。

键盘事件走同一条链，但没有默认反应。树永远是链的最后一环，因此树上的 `KeyDown` 处理器无论目标是哪个组件都能听到路由过的按键。

```csharp
var input = WorkflowInput.For(tree);

if (tree.GetHelper() is IInputEvents events)
{
    events.Input.KeyDown += (_, e) =>
    {
        if (e.Key == InputKey.Delete && e.Target is ILinkComponent link)
        {
            link.DeleteCommand.Execute(null);
            e.Handle.PreventDefault = true;
        }
    };
}
```

**预期结果：** 任意组件是指针目标时按下的键都会到达树的中继；处理器可用 `StopPropagation` 阻止继续冒泡。

## IInputEvents

**签名：** `interface IInputEvents`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Input` | `InputRelay` | 输入事件路由经过该组件时它收到的事件。 |

该接口与 Helper 接口分离：已有 Helper 实现者不会因此破坏，不需要输入的 Helper 也无需回应它。派生自 `NodeHelper<T>` 及其兄弟的 Helper 已经实现了它。

## InputRelay

**签名：** `sealed class InputRelay`

| 事件 | 参数 |
| --- | --- |
| `PointerEntered` | `EventHandler<PointerEnteredEventArgs>` |
| `PointerExited` | `EventHandler<PointerExitedEventArgs>` |
| `PointerMoved` | `EventHandler<PointerMovedEventArgs>` |
| `PointerPressed` | `EventHandler<PointerPressedEventArgs>` |
| `PointerReleased` | `EventHandler<PointerReleasedEventArgs>` |
| `PointerWheelChanged` | `EventHandler<PointerWheelEventArgs>` |
| `KeyDown` | `EventHandler<KeyDownEventArgs>` |
| `KeyUp` | `EventHandler<KeyUpEventArgs>` |

`sender` 是该中继，订阅者据此判断自己听到的是路由的哪一级。一个参数实例在路由的每一级各触发一次。

## WorkflowEventHandle

**签名：** `sealed class WorkflowEventHandle`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `PreventDefault` | `bool` | 拒绝一个 `…ing` 模型动作，或在路由输入上让框架自身的动作停手；对 `…ed` 报告无效。 |
| `StopPropagation` | `bool` | 在路由输入上，祖先不再听到；在 `…ed` 报告上，后续订阅者不再听到。框架自身处理不受影响。 |

一个句柄随一个逻辑动作走，而不是随一条事件走，因此路由后方的订阅者能读到前方订阅者的决定。

```csharp
input.Route(new PointerWheelEventArgs(
    new Anchor(120, 80, 0),
    InputModifiers.Shift,
    source: null,
    target: tree.Nodes[0],
    deltaX: 0d,
    deltaY: 120d,
    handle: new WorkflowEventHandle()));
```

**预期结果：** 滚轮参数先到达节点的中继，再到达树的中继；设置 `PreventDefault` 的处理器会让适配器跳过该格的自身滚动。
