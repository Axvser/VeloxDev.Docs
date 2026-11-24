# 输入事件参数

适配器每个动作构造一个参数并交给 `WorkflowInput.Route`。每个参数都携带位置或按键、修饰键、来源视图、目标组件，以及与整条路由共享的 `WorkflowEventHandle`。基类构造函数为 `protected`；适配器实例化的是具体子类。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## PointerEventArgs

**签名：** `abstract class PointerEventArgs : EventArgs`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Position` | `Anchor` | 指针位置，包含层。 |
| `Modifiers` | `InputModifiers` | 按下的修饰键。 |
| `Source` | `object?` | 输入来源视图；平台没有时为 `null`。 |
| `Target` | `IWorkflowComponent?` | 指针所在的组件；空白画布为 `null`。 |
| `Handle` | `WorkflowEventHandle` | 该动作的句柄。 |

**受保护签名：** `PointerEventArgs(Anchor position, InputModifiers modifiers, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)`

### 具体指针参数

| 类型 | 构造函数 | 额外成员 |
| --- | --- | --- |
| `PointerEnteredEventArgs` | `(Anchor position, InputModifiers modifiers, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)` | — |
| `PointerExitedEventArgs` | 同上五个参数 | — |
| `PointerMovedEventArgs` | 同上五个参数 | — |
| `PointerPressedEventArgs` | `(Anchor, InputModifiers, object?, IWorkflowComponent?, MouseButton button, int clickCount, WorkflowEventHandle)` | `Button`（`MouseButton`）、`ClickCount`（`int`） |
| `PointerReleasedEventArgs` | 与按下相同 | `Button`、`ClickCount` |
| `PointerWheelEventArgs` | `(Anchor, InputModifiers, object?, IWorkflowComponent?, double deltaX, double deltaY, WorkflowEventHandle)` | `DeltaX`、`DeltaY`（`double`） |

`PointerWheelEventArgs.DeltaX` 向右为正；`DeltaY` 远离用户为正。没有倾斜滚轮的鼠标报告 `DeltaX == 0`。

```csharp
var pressed = new PointerPressedEventArgs(
    new Anchor(120, 80, 0), InputModifiers.None, source: view, target: node,
    MouseButton.Left, clickCount: 1, new WorkflowEventHandle());

input.Route(pressed);
```

**预期结果：** 节点的 `PointerPressed` 订阅者先于树执行，两者看到同一个 `pressed` 实例。

## KeyEventArgs

**签名：** `abstract class KeyEventArgs : EventArgs`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Key` | `InputKey` | 按键；枚举未命名时为 `InputKey.Unknown`。 |
| `RawKeyCode` | `int` | 平台自身的键码；跨适配器不可比较。 |
| `Modifiers` | `InputModifiers` | 按下的修饰键；即使 `Key` 为 `Unknown` 也精确。 |
| `IsRepeat` | `bool` | 平台是否报告为自动重复。 |
| `Source` | `object?` | 拥有键盘焦点的视图，或 `null`。 |
| `Target` | `IWorkflowComponent?` | 适配器把该键应用到的组件。 |
| `Handle` | `WorkflowEventHandle` | 该动作的句柄。 |

**受保护签名：** `KeyEventArgs(InputKey key, int rawKeyCode, InputModifiers modifiers, bool isRepeat, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)`

| 具体类型 | 构造函数 |
| --- | --- |
| `KeyDownEventArgs` | `(InputKey key, int rawKeyCode, InputModifiers modifiers, bool isRepeat, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)` |
| `KeyUpEventArgs` | 同上七个参数 |

```csharp
var down = new KeyDownEventArgs(
    InputKey.Delete, rawKeyCode: 0, InputModifiers.None, isRepeat: false,
    source: view, target: link, new WorkflowEventHandle());

input.Route(down);
```

**预期结果：** `KeyDown` 先到达连线的中继，再到树；Core 自身不会执行删除。
