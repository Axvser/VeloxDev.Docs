# 工作流系统 — 快速入门

VeloxDev 工作流系统是一个跨平台的视觉化工作流编辑引擎。它提供了完整的构建块 —— **Tree（树）**、**Node（节点）**、**Slot（槽位）**、**Link（连接线）** —— 让你可以在任何 .NET UI 框架上创建交互式流程图编辑器。

## 安装

在项目中添加 VeloxDev.Core 包：

```xml
<PackageReference Include="VeloxDev.Core" Version="6.0.82" />
```

如需特定 UI 框架支持，添加对应适配器：

| 框架 | 包 |
|-----------|---------|
| WPF | `VeloxDev.WPF` |
| Avalonia | `VeloxDev.Avalonia` |
| WinUI | `VeloxDev.WinUI` |
| MAUI | `VeloxDev.MAUI` |

## 基本用法

### 1. 定义 Tree ViewModel

创建一个使用 `[WorkflowBuilder.Tree<T>]` 注解的 partial 类。源代码生成器会自动生成完整的 ViewModel 样板代码。

```csharp
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Tree<MyTreeHelper>]
public partial class MyWorkflowTree
{
	public MyWorkflowTree() => InitializeWorkflow();
}

public class MyTreeHelper : TreeHelper<MyWorkflowTree>
{
	// Tree 级生命周期钩子
	public override void Install(IWorkflowTreeViewModel tree)
	{
		base.Install(tree);
		// 初始化服务、Agent 等
	}

	public override IWorkflowLinkViewModel CreateLink(
		IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)
	{
		return new MyLink { Sender = sender, Receiver = receiver };
	}
}
```

### 2. 定义 Node 和 Slot ViewModel

```csharp
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Node<MyNodeHelper>]
public partial class MyNode
{
	// 自动生成: Anchor, Size, Slots, Commands
}

public class MyNodeHelper : NodeHelper<MyNode>
{
	public override Task WorkAsync(object? parameter, CancellationToken ct)
	{
		// 该节点处理工作时的业务逻辑
		return Task.CompletedTask;
	}
}

[WorkflowBuilder.Slot<MySlotHelper>]
public partial class MySlot { }

public class MySlotHelper : SlotHelper<MySlot> { }
```

### 3. 设置 UI（Avalonia 示例）

在 XAML/AXAML 视图中使用提供的附加行为：

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

为节点类型定义数据模板：

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

### 4. 添加和连接节点

```csharp
// 向 Tree 添加节点
var node = new MyNode { Anchor = new Anchor(100, 50), Size = new Size(200, 100) };
tree.CreateNodeCommand.Execute(node);

// 在节点上创建槽位
var inputSlot = new MySlot { Channel = SlotChannel.Input };
node.CreateSlotCommand.Execute(inputSlot);

var outputSlot = new MySlot { Channel = SlotChannel.Output };
node.CreateSlotCommand.Execute(outputSlot);

// 连接槽位（从 Tree 发起）
tree.SendConnectionCommand.Execute(outputSlot);   // 标记为发送方
tree.ReceiveConnectionCommand.Execute(inputSlot);  // 完成连接
```

### 5. 序列化与反序列化

```csharp
using VeloxDev.MVVM.Serialization;

// 序列化
var json = tree.Serialize();
await File.WriteAllTextAsync("workflow.json", json);

// 反序列化
var copy = json.Deserialize<MyWorkflowTree>();
copy.Layout.UpdateCommand.Execute(null);  // 恢复布局
```

## 平台特定行为

所有平台共享同一套附加行为：

| 行为 | 用途 |
|----------|---------|
| `WorkflowSurfaceBehavior` | 启用画布平移/缩放、滚动同步、小地图 |
| `WorkflowNodeDragBehavior` | 启用节点拖拽移动 |
| `WorkflowSlotConnectionBehavior` | 启用点击槽位连接 |
| `WorkflowSlotLayoutBehavior` | 自动排列节点上的槽位位置 |
| `WorkflowCanvasTransformBehavior` | 提供平移/缩放的渲染变换 |
| `ViewPool` | 虚拟化 —— 仅渲染可见项目 |
| `WorkflowMinimapOverlay` | 小地图概览面板 |

## 进一步阅读

- 查看 [API 参考](../../2_API参考/0_工作流系统/index.md) 了解详细接口文档
- 查看 [架构分析](../../3_架构分析/1_功能地图/0_工作流系统/index.md) 了解架构和设计模式
