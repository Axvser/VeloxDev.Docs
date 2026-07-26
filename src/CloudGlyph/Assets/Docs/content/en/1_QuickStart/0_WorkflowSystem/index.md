# WorkflowSystem — Quick Start

VeloxDev WorkflowSystem is a cross-platform visual workflow editing engine. It provides a complete set of building blocks — **Tree**, **Node**, **Slot**, **Link** — for creating interactive flowchart-like editors on any .NET UI framework.

## Installation

Add the VeloxDev.Core package to your project:

```xml
<PackageReference Include="VeloxDev.Core" Version="6.0.82" />
```

For a specific UI framework, add the corresponding adapter:

| Framework | Package |
|-----------|---------|
| WPF | `VeloxDev.WPF` |
| Avalonia | `VeloxDev.Avalonia` |
| WinUI | `VeloxDev.WinUI` |
| MAUI | `VeloxDev.MAUI` |

## Basic Usage

### 1. Define a Tree ViewModel

Create a partial class annotated with `[WorkflowBuilder.Tree<T>]`. The source generator produces the full ViewModel boilerplate.

```csharp
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Tree<MyTreeHelper>]
public partial class MyWorkflowTree
{
	public MyWorkflowTree() => InitializeWorkflow();
}

public class MyTreeHelper : TreeHelper<MyWorkflowTree>
{
	// Tree-level lifecycle hooks
	public override void Install(IWorkflowTreeViewModel tree)
	{
		base.Install(tree);
		// Initialize services, agents, etc.
	}

	public override IWorkflowLinkViewModel CreateLink(
		IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)
	{
		return new MyLink { Sender = sender, Receiver = receiver };
	}
}
```

### 2. Define Node and Slot ViewModels

```csharp
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Node<MyNodeHelper>]
public partial class MyNode
{
	// Auto-generated: Anchor, Size, Slots, Commands
}

public class MyNodeHelper : NodeHelper<MyNode>
{
	public override Task WorkAsync(object? parameter, CancellationToken ct)
	{
		// Business logic executed when this node processes work
		return Task.CompletedTask;
	}
}

[WorkflowBuilder.Slot<MySlotHelper>]
public partial class MySlot { }

public class MySlotHelper : SlotHelper<MySlot> { }
```

### 3. Set Up the UI (Avalonia Example)

In your XAML/AXAML view, use the provided attached behaviors:

```xml
<UserControl xmlns="https://github.com/avaloniaui"
			 xmlns:behaviors="using:VeloxDev.WorkflowSystem.AttachedBehaviors"
			 xmlns:workflow="using:VeloxDev.WorkflowSystem"
			 behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
			 behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
			 behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas">

	<Grid>
		<ScrollViewer x:Name="PART_ScrollViewer">
			<Canvas x:Name="PART_Canvas"
					Width="{Binding Layout.ActualSize.Width}"
					Height="{Binding Layout.ActualSize.Height}"
					behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}">
			</Canvas>
		</ScrollViewer>
		<behaviors:WorkflowMinimapOverlay ScrollViewerName="PART_ScrollViewer"
										  WorkflowTree="{Binding}" />
	</Grid>
</UserControl>
```

Define data templates for your node types:

```xml
<UserControl.DataTemplates>
	<DataTemplate DataType="local:MyNode">
		<local:MyNodeView Width="{Binding Size.Width}"
						  Height="{Binding Size.Height}"
						  Canvas.Left="{Binding Anchor.Horizontal}"
						  Canvas.Top="{Binding Anchor.Vertical}" />
	</DataTemplate>
<DataTemplate DataType="workflow:IWorkflowLinkViewModel">
		<local:BezierCurveView StartLeft="{Binding Sender.Anchor.Horizontal}"
							   StartTop="{Binding Sender.Anchor.Vertical}"
							   EndLeft="{Binding Receiver.Anchor.Horizontal}"
							   EndTop="{Binding Receiver.Anchor.Vertical}" />
	</DataTemplate>
</UserControl.DataTemplates>
```

### 4. Add and Connect Nodes

```csharp
// Add a node to the tree
var node = new MyNode { Anchor = new Anchor(100, 50), Size = new Size(200, 100) };
tree.CreateNodeCommand.Execute(node);

// Create slots on the node
var inputSlot = new MySlot { Channel = SlotChannel.Input };
node.CreateSlotCommand.Execute(inputSlot);

var outputSlot = new MySlot { Channel = SlotChannel.Output };
node.CreateSlotCommand.Execute(outputSlot);

// Connect slots (initiate from the tree)
tree.SendConnectionCommand.Execute(outputSlot);   // Mark as sender
tree.ReceiveConnectionCommand.Execute(inputSlot);  // Complete connection
```

### 5. Serialize and Deserialize

```csharp
using VeloxDev.MVVM.Serialization;

// Serialize
var json = tree.Serialize();
await File.WriteAllTextAsync("workflow.json", json);

// Deserialize
var copy = json.Deserialize<MyWorkflowTree>();
copy.Layout.UpdateCommand.Execute(null);  // Restore layout
```

## Platform-Specific Behaviors

All platforms share the same set of attached behaviors:

| Behavior | Purpose |
|----------|---------|
| `WorkflowSurfaceBehavior` | Enables surface pan/zoom, scroll synchronization, minimap |
| `WorkflowNodeDragBehavior` | Enables drag-to-move on nodes |
| `WorkflowSlotConnectionBehavior` | Enables click-to-connect on slots |
| `WorkflowSlotLayoutBehavior` | Auto-layouts slot positions on nodes |
| `WorkflowCanvasTransformBehavior` | Provides the render transform for pan/zoom |
| `ViewPool` | Virtualization — only renders visible items |
| `WorkflowMinimapOverlay` | Minimap overview panel |

## Next Steps

- See the [API Reference](../../2_API/0_WorkflowSystem/index.md) for detailed interface documentation
- See the [SE Analysis](../../3_SE_Analysis/1_feature_map/0_WorkflowSystem/index.md) for architecture and design patterns
