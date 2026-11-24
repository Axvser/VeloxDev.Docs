# Default view models

`VeloxDev.WorkflowSystem` ships one sealed implementation per component role and the attributes that make the source generator emit the same members on a host's partial class. The generated path is preferred because it writes the ports, helper installation and command plumbing from the class declaration.

## Generator attributes

All four attributes are nested in `public sealed class WorkflowBuilder`; the generic argument is the helper type.

| Attribute | Type parameter | Public property |
| --- | --- | --- |
| `WorkflowBuilder.TreeAttribute<T>` | `T : ITreeHelper, new()` | `VirtualLinkType` (`Type?`), `VirtualSlotType` (`Type?`) |
| `WorkflowBuilder.NodeAttribute<T>` | `T : INodeHelper, new()` | `Semaphore` (`int`, default `1`) — concurrent capacity of the receive task |
| `WorkflowBuilder.SlotAttribute<T>` | `T : ISlotHelper, new()` | none |
| `WorkflowBuilder.LinkAttribute<T>` | `T : ILinkHelper, new()` | `SlotType` (`Type?`) — starter slot type for a new link |

Two layout-seed attributes live in the same namespace and are baked into the generated backing-field initializer:

| Attribute | Constructor | Public properties |
| --- | --- | --- |
| `DefaultAnchorAttribute` | `(double horizontal = 0, double vertical = 0, int layer = 0)` | `Horizontal`, `Vertical`, `Layer` |
| `DefaultSizeAttribute` | `(double width = 0, double height = 0)` | `Width`, `Height` |

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

The generator also emits `InitializeWorkflow()`, `GetHelper()`, `SetHelper(...)`, the four command properties of the role, `RuntimeId`, and the `Parent`/`Slots`/`Targets`/`Sources` collections. A `[VeloxProperty]` member typed `ISlotComponent` becomes a port: the generated `InitializeWorkflowCore` creates the slot, sets its `Parent` and adds it to `Slots`.

## TreeDefaultViewModel

**Signature:** `sealed partial class TreeDefaultViewModel : ITreeComponent, IRuntimeIdentifiable`

| Member | Type | Description |
| --- | --- | --- |
| `TreeDefaultViewModel()` | constructor | Calls `InitializeWorkflow()`, installing `TreeHelper`. |
| `Helper` | `ITreeHelper` | The installed helper; private setter. |
| `RuntimeId` | `string` | New GUID (`"N"` format) at construction. |
| `GetHelper()` / `SetHelper(ITreeHelper)` | `ITreeHelper` / `void` | Replaces the helper with uninstall/install. |
| `InitializeWorkflow()` | `void` | Installs the default `TreeHelper`. |

Interface state defaults: `Layout` is a new `CanvasLayout`; `VirtualLink` is a `LinkDefaultViewModel` with two `SlotDefaultViewModel` ends; `Nodes`, `Links` and `LinksMap` start empty. `SetPointer` ignores a parameter that is not an `Anchor`; `CreateNode` ignores a non-`INodeComponent`.

## NodeDefaultViewModel

**Signature:** `sealed partial class NodeDefaultViewModel : INodeComponent, IRuntimeIdentifiable`

| Member | Type | Description |
| --- | --- | --- |
| `NodeDefaultViewModel()` | constructor | Installs `NodeHelper`. |
| `Helper` | `INodeHelper` | The installed helper. |
| `RuntimeId` | `string` | New GUID at construction. |
| `Anchor` / `Size` | `Anchor` / `Size` | Hand-written: the getter returns `value.Collapse(Parent?.Layout?.Scale)`; the setter stores the world value and raises `PropertyChanging`/`PropertyChanged`. |
| `GetHelper()` / `SetHelper(INodeHelper)` / `InitializeWorkflow()` | | Same contract as the tree. |

`Anchor` and `Size` raise `OnAnchorChanging`/`OnAnchorChanged`, `OnSizeChanging`/`OnSizeChanged` partial hooks. `Parent` change re-attaches a scale tracker, so a zoom change re-raises both geometry notifications. `Receive` wraps a non-`ITaskContext` parameter in `new TaskContext(parameter)`.

## SlotDefaultViewModel

**Signature:** `sealed partial class SlotDefaultViewModel : ISlotComponent, IRuntimeIdentifiable`

Defaults: `Targets` and `Sources` empty; `Parent` null; `Channel = SlotChannel.OneBoth`; `State = SlotState.StandBy`; `Anchor = new Anchor(double.NaN, double.NaN, 0)` (unmeasured). Commands forward to `SlotHelper`: `SetChannel`, `SendConnection`, `ReceiveConnection`, `Delete`, `Close`. `InitializeWorkflow` installs `SlotHelper`.

## LinkDefaultViewModel

**Signature:** `sealed partial class LinkDefaultViewModel : IConnectionPreviewLink, IRuntimeIdentifiable`

Defaults: `Sender` and `Receiver` are new `SlotDefaultViewModel` instances; `IsVisible = false`. Commands: `Delete`, `Close`.

| Member | Type | Description |
| --- | --- | --- |
| `Preview` | `ConnectionPreviewState` | Current drag stage. |
| `SetPreview(ConnectionPreviewState)` | `void` | Called by `WorkflowInput`; raises `PropertyChanged` for `Preview` when it changes. |

Because it implements `IConnectionPreviewLink`, a virtual link of this type can paint itself from the same state the input route maintains (see [Connection preview](../../02_connection-rules-preview/01_connection-preview/index.md)).

## Example

```csharp
var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0), Size = new Size(220, 120) };
tree.GetHelper().CreateNode(node);

Console.WriteLine($"{tree.Nodes.Count} {node.Slots.Count} {node.RuntimeId.Length > 0}");
tree.Layout.Scale = new Scale(0.5, 0.5);
Console.WriteLine($"{node.Anchor} {node.GetWorldAnchor()}");
```

The generator path and the default models are interchangeable at the interface boundary; a host that needs custom ports and commands uses the generated partial class, while a host that only needs a graph uses these sealed types directly.
