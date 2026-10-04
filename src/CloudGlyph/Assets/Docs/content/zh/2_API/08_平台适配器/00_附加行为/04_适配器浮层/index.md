# API — 附加行为 · 适配器特有的覆盖层与宿主

除共享行为集合外，部分适配器还额外提供工作流视图类型，替换或扩展公共表面的某一部分。

## 类：`WorkflowLinkOverlay`（MAUI）

MAUI 在一个视口大小的 `GraphicsView` 里绘制那些**没有自己视图**的连接 —— 立即模式宿主，以及池化连接视图尚未实例化出来的那几帧。已经把自己的曲线连同绘制它的控件一起发布的连接由那个控件绘制，这里跳过。源码：`Src/Adapters/VeloxDev.MAUI/Attached/Workflow/WorkflowLinkOverlay.cs`。

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
| `LinkFlowEnabled` | `bool` | 开关沿曲线流动的光带动画。 |
| `InteractionSource` | `View?` | 已在表面输入路径上的视图，用来把悬停/按下转发给命中测试（覆盖层自身保持 `InputTransparent`）。 |
| `SelectedLinkColor` | `Color?` | 悬停/选中连接的描边。 |

覆盖层用 MAUI 图形 `IDrawable` 模型（`Draw(ICanvas canvas, RectF dirtyRect)`）把每条连接画成一条三次贝塞尔曲线；流动的光带是按弧长从该曲线上裁出来的，而不是沿折线映射。它是纯绘制层（`VisualElement.InputTransparent` 恒为 `true`，视口大小的视图因此不会吞掉画布手势）；交互经 `InteractionSource` 驱动 —— 悬停一条连接即选中它，`Delete` 删除它，右键（非 Windows 上是长按）转发给 `LinkInteraction`，由宿主表面弹出自己的菜单。*确切的拖拽/重排语义属 `*推断所得*` —— 未经自动化 Demo 驱动。*

## 类：`WorkflowGridDecorator`（Jalium）

Jalium 提供现成的网格/标尺装饰层（WPF/Avalonia/WinUI/WinForms 改由 `*-v-decorator` 模板或各角色基类获得）。源码：`Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowGridDecorator.cs`。它是一个纯绘制/配置类（无基类型，**也不实现** `IWorkflowGridDecorator`）；复合控件 `WorkflowTreeView` 经自身的 `GridDecorator` 属性持有它。Razor 有同名组件（`WorkflowGridDecorator.razor` + `.razor.cs`）。

```csharp
public class WorkflowGridDecorator
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `RulerThickness` | `const double`（36） | 标尺带厚度。 |
| `MinorGridColor` / `MajorGridColor` / `AxisColor` | `Color` | 网格配色。 |
| `RulerBackground` / `RulerLabelColor` / `RulerTickColor` / `RulerDividerColor` | `Color` | 标尺配色。 |
| `GridStep` | `double` | 次要网格间距。 |
| `MajorLineEvery` | `int` | 每 N 条次要线为一条主线。 |
| `MajorStep` | `double`（get） | `GridStep * Math.Max(1, MajorLineEvery)`。 |

## 类：`WorkflowTreeView`（Jalium）

整个工作流编辑器的复合宿主控件，也是 Jalium 的**全部**表面 —— Jalium 没有独立的 `WorkflowSurfaceBehavior`。源码：`Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowTreeView.cs`。

```csharp
public class WorkflowTreeView : Canvas
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Tree` | `IWorkflowTreeViewModel?`（get） | 当前挂上的工作流树。 |
| `PortLayout` | `WorkflowPortLayout` | 各角色基类共用的设计期端口布局。 |
| `GridDecorator` | `WorkflowGridDecorator` | 网格/标尺装饰层。 |
| `TemplateSelector` | `IWorkflowTemplateSelector?` | 节点/连接视图工厂；须在 `SetTree` 前设置。 |
| `OriginX` / `OriginY` | `double`（get） | 世界原点加上标尺带。 |
| `ContentOriginX` / `ContentOriginY` | `double`（get） | 世界原点（`Layout.ActualOffset`）。 |
| `AttachScrollViewer(ScrollViewer)` | 方法 | 接线驱动平移的滚动查看器。 |
| `SetTree(IWorkflowTreeViewModel?)` | 方法 | 挂上树并接好视图池。 |
| `NotifyZoomCommitted(hx, vy)` | 方法 | 宿主处理完捏合/滚轮后施加缩放枢轴。 |
| `NavigateToWorld(wx, wy)` | 方法 | 滚动到某个世界点可见。 |
| `OnBuildLinkMenu` | `protected virtual void` | 每次右键时构建连线右键菜单；基类只加一个 **Delete** 条目 —— 重写它来增删条目。 |

与另外六家不同，Jalium 不按名字解析 `PART_*` 部件，也不施加静态表面行为：它从模型算端口几何、给视图定位（不做视觉测量），因此树视图本身就是表面。

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
