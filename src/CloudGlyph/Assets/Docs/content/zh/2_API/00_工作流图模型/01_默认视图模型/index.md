# 默认视图模型

`VeloxDev.WorkflowSystem` 为每个组件角色提供一个 sealed 实现，以及让源生成器在宿主的 partial 类上产出同样成员的特性。推荐走生成路径：它从类声明写出端口、助手安装与命令管线。

## 生成器特性

四个特性都嵌套在 `public sealed class WorkflowBuilder` 中；泛型实参是助手类型。

| 特性 | 类型参数 | 公开属性 |
| --- | --- | --- |
| `WorkflowBuilder.TreeAttribute<T>` | `T : ITreeHelper, new()` | `VirtualLinkType`（`Type?`）、`VirtualSlotType`（`Type?`） |
| `WorkflowBuilder.NodeAttribute<T>` | `T : INodeHelper, new()` | `Semaphore`（`int`，默认 `1`）—— 接收任务的并发容量 |
| `WorkflowBuilder.SlotAttribute<T>` | `T : ISlotHelper, new()` | 无 |
| `WorkflowBuilder.LinkAttribute<T>` | `T : ILinkHelper, new()` | `SlotType`（`Type?`）—— 新连线的起始插槽类型 |

同命名空间还有两个布局种子特性，其值会写入生成的字段初始值：

| 特性 | 构造函数 | 公开属性 |
| --- | --- | --- |
| `DefaultAnchorAttribute` | `(double horizontal = 0, double vertical = 0, int layer = 0)` | `Horizontal`、`Vertical`、`Layer` |
| `DefaultSizeAttribute` | `(double width = 0, double height = 0)` | `Width`、`Height` |

```csharp
[WorkflowBuilder.Node<NodeHelper>]
[DefaultSize(220, 120)]
[DefaultAnchor(60, 80, 0)]
public partial class DemoNode
{
    public DemoNode() => InitializeWorkflow();
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}
```

生成器还会产出 `InitializeWorkflow()`、`GetHelper()`、`SetHelper(...)`、该角色的四个命令属性、`RuntimeId`，以及 `Parent`/`Slots`/`Targets`/`Sources` 集合。类型为 `ISlotComponent` 的 `[VeloxProperty]` 成员会成为一个端口：生成的 `InitializeWorkflowCore` 创建插槽、设置其 `Parent` 并加入 `Slots`。

## TreeDefaultViewModel

**签名：** `sealed partial class TreeDefaultViewModel : ITreeComponent, IRuntimeIdentifiable`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `TreeDefaultViewModel()` | 构造函数 | 调用 `InitializeWorkflow()`，安装 `TreeHelper`。 |
| `Helper` | `ITreeHelper` | 已安装的助手；private setter。 |
| `RuntimeId` | `string` | 构造时的新 GUID（`"N"` 格式）。 |
| `GetHelper()` / `SetHelper(ITreeHelper)` | `ITreeHelper` / `void` | 经卸载/安装替换助手。 |
| `InitializeWorkflow()` | `void` | 安装默认 `TreeHelper`。 |

接口状态默认值：`Layout` 为新的 `CanvasLayout`；`VirtualLink` 为两端各一个 `SlotDefaultViewModel` 的 `LinkDefaultViewModel`；`Nodes`、`Links`、`LinksMap` 为空。`SetPointer` 忽略非 `Anchor` 参数；`CreateNode` 忽略非 `INodeComponent` 参数。

## NodeDefaultViewModel

**签名：** `sealed partial class NodeDefaultViewModel : INodeComponent, IRuntimeIdentifiable`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `NodeDefaultViewModel()` | 构造函数 | 安装 `NodeHelper`。 |
| `Helper` | `INodeHelper` | 已安装的助手。 |
| `RuntimeId` | `string` | 构造时的新 GUID。 |
| `Anchor` / `Size` | `Anchor` / `Size` | 手写实现：getter 返回 `value.Collapse(Parent?.Layout?.Scale)`；setter 存储世界值并触发 `PropertyChanging`/`PropertyChanged`。 |
| `GetHelper()` / `SetHelper(INodeHelper)` / `InitializeWorkflow()` | | 与树的契约相同。 |

`Anchor` 与 `Size` 会触发 `OnAnchorChanging`/`OnAnchorChanged`、`OnSizeChanging`/`OnSizeChanged` 分部钩子。`Parent` 变化会重新挂载缩放跟踪器，因此缩放变化会重新触发两个几何通知。`Receive` 会把非 `ITaskContext` 参数包进 `new TaskContext(parameter)`。

## SlotDefaultViewModel

**签名：** `sealed partial class SlotDefaultViewModel : ISlotComponent, IRuntimeIdentifiable`

默认值：`Targets` 与 `Sources` 为空；`Parent` 为 null；`Channel = SlotChannel.OneBoth`；`State = SlotState.StandBy`；`Anchor = new Anchor(double.NaN, double.NaN, 0)`（未测量）。命令转发给 `SlotHelper`：`SetChannel`、`SendConnection`、`ReceiveConnection`、`Delete`、`Close`。`InitializeWorkflow` 安装 `SlotHelper`。

## LinkDefaultViewModel

**签名：** `sealed partial class LinkDefaultViewModel : IConnectionPreviewLink, IRuntimeIdentifiable`

默认值：`Sender` 与 `Receiver` 各为新的 `SlotDefaultViewModel`；`IsVisible = false`。命令：`Delete`、`Close`。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Preview` | `ConnectionPreviewState` | 当前拖拽阶段。 |
| `SetPreview(ConnectionPreviewState)` | `void` | 由 `WorkflowInput` 调用；变化时触发 `Preview` 的 `PropertyChanged`。 |

由于实现了 `IConnectionPreviewLink`，这种临时连线可以按输入路由维护的同一状态自绘（见[连接预览](../../02_连接规则与预览/01_连接预览/index.md)）。

## 示例

```csharp
var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0), Size = new Size(220, 120) };
tree.GetHelper().CreateNode(node);

Console.WriteLine($"{tree.Nodes.Count} {node.Slots.Count} {node.RuntimeId.Length > 0}");
tree.Layout.Scale = new Scale(0.5, 0.5);
Console.WriteLine($"{node.Anchor} {node.GetWorldAnchor()}");
```

生成路径与默认模型在接口边界上可互换；需要自定义端口与命令的宿主用生成的 partial 类，只需要一张图的宿主直接用这些 sealed 类型。
