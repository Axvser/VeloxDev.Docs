# API — 附加行为 · 适配器特有的覆盖层与宿主

除共享行为集合外，部分适配器还额外提供工作流视图类型，替换或扩展公共表面的某一部分。

## 类：`WorkflowLinkOverlay`（MAUI）

MAUI 把工作流连接渲染成专用图形层，而非每条连接独立的视觉元素。源码：`Src/Adapters/VeloxDev.MAUI/Attached/Workflow/WorkflowLinkOverlay.cs`。

```csharp
public sealed class WorkflowLinkOverlay : GraphicsView
```

可绑定属性 / CLR 属性：

| 属性 | 类型 | 说明 |
|---|---|---|
| `WorkflowTree` | `IWorkflowTreeViewModel?` | 要绘制的连接的树。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 滚动偏移（由表面推送）。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 画布内容偏移。 |
| `RulerThickness` | `double` | 绘制时要跳过的标尺带内缩。 |
| `LinkLineColor` | `Color?` | 实线连接描边。 |
| `VirtualLineColor` | `Color?` | 虚拟 / 超出可达范围连接段所用描边。 |
| `StrokeWidth` | `double` | 连接描边宽度。 |

覆盖层用 MAUI 图形 `IDrawable` 模型绘制连接折线（`Draw(ICanvas canvas, RectF dirtyRect)`），包括箭头。它是 XAML 适配器挂到各连接视图上的连接视觉在 MAUI 上的转发表面。*确切的拖拽/重排语义属 `*推断所得*` —— 未经自动化 Demo 驱动。*

## 类：`WorkflowGridDecorator`（Jalium）

Jalium 提供现成的网格/标尺装饰元素（WPF/Avalonia/WinUI 改由 `*-v-decorator` 模板获得）。源码：`Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowGridDecorator.cs`。

```csharp
public class WorkflowGridDecorator : Decorator, IWorkflowGridDecorator
```

依赖属性：

| 属性 | 类型 | 说明 |
|---|---|---|
| `RulerThickness` | `double` | 标尺带厚度。 |
| `GridSpacing` | `double` | 次要网格间距。 |
| `MajorLineEvery` | `int` | 每 N 条次要线为一条主线。 |
| `ScrollOffsetX` / `ScrollOffsetY` / `ContentOffsetX` / `ContentOffsetY` | `double` | `IWorkflowGridDecorator` 偏移。 |

它还暴露 `RulerBand => RulerThickness`（接口的只读带厚度，用于虚拟化内缩）。

## 类：`WorkflowTreeView`（Jalium）

现成的整个工作流编辑器复合宿主控件。源码：`Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowTreeView.cs`。

```csharp
public class WorkflowTreeView : Grid
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `PART_SurfaceBorder` | `Border`（get） | 表面边框。 |
| `PART_ScrollViewer` | `ScrollViewer`（get） | 内部滚动查看器（自动滚动条、透明背景）。 |
| `PART_Canvas` | `Canvas`（get） | 节点/连接画布。 |
| `PART_GridDecorator` | `FrameworkElement`（get） | 活动网格装饰层。 |
| `PART_MinimapOverlay` | `FrameworkElement?`（get） | 活动小地图覆盖层。 |
| `TemplateSelector` | `IWorkflowTemplateSelector?` | 节点/连接视图工厂；须在赋值 `ViewModel` 前设置。 |
| `ViewModel` | `IWorkflowTreeViewModel?` | 工作流树；设置它也会设置 `DataContext`。 |
| `GridDecorator`（set） | `IWorkflowGridDecorator?` | 换入带样式的网格装饰层。 |
| `MinimapOverlay`（set） | `IWorkflowMinimapOverlay?` | 添加带样式的小地图覆盖层。 |

它还承载表面行为：内部接线把 `WorkflowSurfaceBehavior` 应用到命名的 `PART_*` 部件上，使平移、缩放与视口数据推送只需一个控件。

## 接口：`IWorkflowTemplateSelector`（WinForms / Jalium）

附加行为命名空间里的模板选择工厂（WinForms：`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/ViewManager.cs`；Jalium：`Src/Adapters/VeloxDev.Jalium/Attached/Workflow/IWorkflowTemplateSelector.cs`）。

| 适配器 | 成员 |
|---|---|
| WinForms | `Control CreateView(object item)` |
| Jalium | `FrameworkElement CreateView(object item)` |

## Razor 组件辅助

Razor 在组件行为旁提供两个小静态辅助类，均位于 `VeloxDev.WorkflowSystem.AttachedBehaviors`：

### `WorkflowGeometryScope`

在缩放事务期间压制逐节点几何写入，使原子的 `applyZoomSurface` 浏览器帧成为该手势唯一的几何权威。

| 成员 | 签名 | 说明 |
|---|---|---|
| `IsZooming` | `static bool` | 当前异步流上是否有缩放事务进行中。 |
| `Zoom()` | `static IDisposable` | 进入事务；释放返回的句柄以退出。 |

使用 `AsyncLocal<int>`（绝不是普通静态标志），使共享进程的 Blazor Server 回路互不可见对方的缩放。

### `WorkflowRuntimeIds`

按引用为工作流组件分配稳定、进程生命期唯一的 id（弱持有），使 Blazor 元素可携带 `data-*-id` 属性经 JavaScript 往返，再解析回同一对象。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Get` | `static string Get(object component)` | 稳定 id，首次使用时分配一个。 |
| `TryFind` | `static bool TryFind<T>(string? id, out T? value) where T : class` | 由先前分配的 id 解析回组件。 |
| `Enumerate` | `static IEnumerable<KeyValuePair<object, string>> Enumerate()` | 所有已注册 id（诊断/测试用）。 |
