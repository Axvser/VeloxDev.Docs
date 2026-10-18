# API — 附加行为 · 节点拖拽与槽行为

让工作流可交互的三个行为：拖拽节点、连接槽、让槽锚点对齐节点布局。全部位于 `VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 类：`WorkflowNodeDragBehavior`

让节点可拖拽。按下时捕获指针；移动时执行 `node.MoveCommand.Execute(new Offset(current - last))`；松开/丢失捕获时停止。

附加属性（WPF / Avalonia / WinUI / MAUI / Jalium 用各自原生属性系统；Razor 为组件）：

| 属性 | 类型 | 说明 |
|---|---|---|
| `IsEnabled` | 附加 `bool` | 启用捕获与移动处理。 |
| `CoordinateHostName` | 附加 `string?` | 计算增量时使用的坐标空间元素名。 |
| `CoordinateHostType` | 附加 `Type?` | 回退宿主类型；默认为 `Canvas`。 |

| 适配器 | 形态 / 说明 |
|---|---|
| WPF | `sealed class : DependencyObject`；getter `GetIsEnabled(DependencyObject)`、`GetCoordinateHostName/Type(...)` |
| Avalonia | `sealed class : AvaloniaObject`；`RegisterAttached<WorkflowNodeDragBehavior, Control, ...>` |
| WinUI | `sealed class : DependencyObject` |
| MAUI | `sealed class`；`BindableProperty.CreateAttached`；getter 接收 `BindableObject` |
| WinForms | `Control` 状态表之上的 `sealed class`（鼠标按下/移动/抬起处理） |
| Jalium | `sealed class : DependencyObject` |

### Razor 组件：`WorkflowNodeDragBehavior`

| 参数 | 类型 | 说明 |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | 要拖拽的节点。 |
| `IsEnabled` | `bool` | 启用拖拽接线。 |
| `Style` | `string?` | 可选 CSS 样式。 |
| `ChildContent` | `RenderFragment?` | 节点内容。 |

公共方法 `OnNodeDrag(double dx, double dy)` 与 `OnNodeDragEnd()` 是执行 `MoveCommand` 的 JS 回调。

## 类：`WorkflowSlotConnectionBehavior`

通过按下/松开连接槽。按下时执行 `slot.SendConnectionCommand.Execute(null)`；松开时执行 `slot.ReceiveConnectionCommand.Execute(null)`。

| 适配器 | 形态 | 额外 |
|---|---|---|
| WPF | `sealed class : DependencyObject`；附加 `IsEnabled`（`bool`） | |
| Avalonia | `sealed class : AvaloniaObject` | |
| WinUI | `sealed class : DependencyObject` | |
| MAUI | `sealed class`；`BindableProperty.CreateAttached` | 另有 `public static void SetIsDraggingConnection(bool)` 全局拖拽标志 setter |
| WinForms | `Control` 状态表之上的 `sealed class` | |
| Jalium | `sealed class : DependencyObject` | |

### Razor 组件：`WorkflowSlotConnectionBehavior`

| 参数 | 类型 | 说明 |
|---|---|---|
| `Slot` | `IWorkflowSlotViewModel?` | 要连接的槽。 |
| `Tree` | `IWorkflowTreeViewModel?` | 用于查找落点目标的树。 |
| `IsEnabled` | `bool` | 启用连接接线。 |
| `Style` | `string?` | 可选 CSS 样式。 |
| `ChildContent` | `RenderFragment?` | 槽内容。 |

公共 JS 回调方法：`OnSlotConnectionStart(double worldX, double worldY)`、`OnSlotConnectionMove(double worldX, double worldY)`、`OnSlotConnectionEnd(string? targetSlotId)`。

### 拖拽期间的连接预览

连接手势通过两个 Core 成员（命名空间 `VeloxDev.WorkflowSystem`）暴露实时候选接收口，而不是适配器类型：

| 成员 | 签名 | 作用 |
|---|---|---|
| `WorkflowTreeEx.StandardSetPreviewReceiver` | `static void StandardSetPreviewReceiver(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel? slot)` | 报告指针下的槽。忽略发送口；候选未变时不重复校验；否则写入 `SlotState.PreviewReceiver` 与 `ConnectionPreviewState`。 |
| `WorkflowTreeEx.StandardRefreshConnectionPreview` | `static void StandardRefreshConnectionPreview(this IWorkflowTreeViewModel component)` | 强制重新校验当前候选（用于宿主的异步结论）。 |
| `WorkflowTreeEx.StandardCheckConnection` | `static ConnectionCheck StandardCheckConnection(this IWorkflowTreeViewModel component, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | 纯预检：方向、同一节点、以及 Helper 的 `ValidateConnection`。 |
| `SlotHitTestEx.HitTest` | `static IWorkflowSlotViewModel? HitTest(IWorkflowTreeViewModel tree, double x, double y, double radius = 12d)` | 半径内最近的已测量槽锚点；跳过 `NaN` 锚点。 |

在 `tree.VirtualLink.IsVisible` 时，各适配器从自己的指针移动路径调用它们：

| 适配器 | 指针移动调用点 |
|---|---|
| WPF | `WorkflowSurfaceBehavior.OnPreviewMouseMove`（先于悬停路由返回） |
| Avalonia | `WorkflowSurfaceBehavior.OnPointerMoved` |
| WinUI | `WorkflowSurfaceBehavior.OnPointerMoved` |
| Jalium | `WorkflowSurfaceBehavior.OnMouseMove` |
| MAUI | `WorkflowSlotConnectionBehavior.UpdatePointer` |
| WinForms | `WorkflowSlotConnectionBehavior.UpdatePointer` |
| Razor | `WorkflowSlotConnectionBehavior.OnSlotConnectionMove`（`[JSInvokable]`） |

```csharp
// 来源：Src/Adapters/VeloxDev.WPF/Attached/Workflow/WorkflowSurfaceBehavior.cs
viewModel.SetPointerCommand.Execute(pointer);

if (viewModel.VirtualLink.IsVisible)
{
    viewModel.StandardSetPreviewReceiver(
        SlotHitTestEx.HitTest(viewModel, pointer.Horizontal, pointer.Vertical));
    return;
}
```

**证据：** Core 测试 `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs` 覆盖了 `StandardSetPreviewReceiver`（候选变化、命中发送口自身、清空）与 `SlotHitTestEx.HitTest`（最近槽、空树）。

## 类：`WorkflowSlotLayoutBehavior`

让槽锚点与节点布局保持同步。它监视节点的 `Anchor` / `Size` / 槽属性，并用 `TranslatePoint` 找到槽中心后重新计算每个槽的 `Anchor`（计入 `Layout.ActualOffset`）。

| 属性 | 类型 | 说明 |
|---|---|---|
| `IsEnabled` | 附加 `bool` | 启用布局同步。 |
| `SlotNames` | 附加 `string?` | 逗号分隔的单个槽控件名（例如 `PART_InputSlot`）。 |
| `SlotEnumeratorNames` | 附加 `string?` | 逗号分隔的、枚举槽的 `ItemsControl` 名（例如 `PART_OutputSlots`）。 |
| `CoordinateHostName` | 附加 `string?` | 计算锚点时的坐标空间。 |
| `CoordinateHostType` | 附加 `Type?` | 回退宿主类型；默认为 `Canvas`。 |

| 适配器 | 形态 |
|---|---|
| WPF | `sealed class : DependencyObject` |
| Avalonia | `sealed class : AvaloniaObject` |
| WinUI | `sealed class : DependencyObject` |
| MAUI | `sealed class`；`BindableProperty.CreateAttached` |
| WinForms | `Control` 状态表之上的 `sealed class` |
| Jalium | `sealed class : DependencyObject` |

### Razor 组件：`WorkflowSlotLayoutBehavior`

| 参数 | 类型 | 说明 |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | 其槽要布局的节点。 |
| `IsEnabled` | `bool` | 启用布局同步。 |
| `CoordinateHostId` | `string?` | 坐标空间元素 id。 |
| `ChildContent` | `RenderFragment?` | 槽内容。 |

公共 JS 回调方法：`OnSlotLayoutBatch(string[][] batch)` 以批处理形式接收重算后的锚点。
