# 平台适配器 — 基本设置 / 注册

用项模板生成工作流视图套件：

```powershell
dotnet new wpf-v-slot -n SlotView -ns MyApp.Views -o Views
dotnet new wpf-v-node -n NodeView -ns MyApp.Views -o Views
dotnet new wpf-v-link -n LinkView -ns MyApp.Views -o Views
dotnet new wpf-v-tree -n TreeView -ns MyApp.Views -o Views
dotnet new wpf-v-selector -n TemplateSelector -ns MyApp.Views -o Views
dotnet new wpf-v-decorator -n GridDecorator -ns MyApp.Views -o Views
dotnet new wpf-v-minimap -n MinimapOverlay -ns MyApp.Views -o Views
```

每个模板都会在 `Views/` 下生成文件，且已经接好所需的 VeloxDev 工作流行为：

- `wpf-v-slot` → `SlotView.xaml/.cs` — `WorkflowSlotConnectionBehavior.IsEnabled="True"`（按下 = 发送，松开 = 接收）。
- `wpf-v-node` → `NodeView.xaml/.cs` — `WorkflowSlotLayoutBehavior`（槽锚点）+ `WorkflowNodeDragBehavior`（拖拽移动）。
- `wpf-v-link` → `LinkView.xaml/.cs` — 被动绘制的折线连接视图。
- `wpf-v-tree` → `TreeView.xaml/.cs` — 画布宿主：`WorkflowSurfaceBehavior`、`ViewPool`、`WorkflowCanvasTransformBehavior`、小地图 + 网格装饰层。
- `wpf-v-selector` → `TemplateSelector.cs` — 针对 Node/Slot/Link/Tree 的 `DataTemplateSelector`。
- `wpf-v-decorator` → `GridDecorator.cs` — `Decorator : IWorkflowGridDecorator`，绘制网格 + 标尺。
- `wpf-v-minimap` → `MinimapOverlay.cs` — `WorkflowMinimapOverlay` 的子类，套用模板颜色。

**预期结果：** `Views/` 下生成七个视图文件，`dotnet build` 能从 `VeloxDev.WPF` 包解析出行为命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors` 并编译通过。
