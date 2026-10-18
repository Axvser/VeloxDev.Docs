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
| `VirtualValidTargetColor` / `VirtualInvalidTargetColor` | `Color?` | 预览候选有效 / 无效时的橡皮筋颜色（`ConnectionPreviewState`）。 |
| `StrokeWidth` | `double` | 连接描边宽度。 |
| `LinkFlowEnabled` | `bool` | 开关沿曲线流动的光带动画。 |
| `InteractionSource` | `View?` | 已在表面输入路径上的视图，用来把悬停/按下转发给命中测试（覆盖层自身保持 `InputTransparent`）。 |

覆盖层用 MAUI 图形 `IDrawable` 模型（`Draw(ICanvas canvas, RectF dirtyRect)`）把每条连接画成一条三次贝塞尔曲线；流动的光带是按弧长从该曲线上裁出来的，而不是沿折线映射。它是纯绘制层（`VisualElement.InputTransparent` 恒为 `true`，视口大小的视图因此不会吞掉画布手势）；交互经 `InteractionSource` 驱动 —— 命中测试记录指针落在哪条连接上，`Delete` 删除它，右键（非 Windows 上是长按）经 `WorkflowInput.For(tree).Route(...)` 以 `PointerPressedEventArgs` 路由，由宿主表面弹出自己的菜单。

**悬停外观归宿主**，这一层只画静息的连接。想让悬停的连接看起来不同的宿主，订阅树的 `IInputEvents` 并在本层之上画自己的一层，曲线取自连接自己发布的那条（`ILinkHitTestable.Curve`）—— 于是两层对「线在哪」永远不会各执一词。*确切的拖拽/重排语义属 `*推断所得*` —— 未经自动化 Demo 驱动。*

## 类：`WorkflowLinkBounds`（Jalium）

Jalium 的连线视图按曲线点定位，而不是从可视元素测量。源码：`Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowLinkBounds.cs`，静态辅助类：

```csharp
public static class WorkflowLinkBounds
{
    public static bool Apply(
        FrameworkElement view,
        IReadOnlyList<Point> canvasLocalPoints,
        out double originX,
        out double originY);
}
```

点集为空时返回 `false`；否则计算点集包围盒、设置视图尺寸与位置（`Canvas.Left` / `Canvas.Top`）、输出原点并返回 `true`。

## Jalium 由模板提供的部件

Jalium **没有**在适配器里提供复合 `WorkflowTreeView`、各角色附加类或网格装饰类。它的表面是共享的静态 `WorkflowSurfaceBehavior`（见[工作流表面](../00_工作流表面/index.md)页），其余由 `dotnet new` 模板提供：

- `jalium-v-decorator` 生成实现 `IWorkflowGridDecorator` 的 `Grid` 子类，带 `RulerThickness`（36）、`GridStep`（40）、`MajorLineEvery`（5）、网格/标尺配色与五个接口偏移成员。
- `jalium-v-selector` 生成带 `NodeTemplate` / `SlotTemplate` / `LinkTemplate` / `TreeTemplate` 的 `DataTemplateSelector`，赋给 `ViewPool.TemplateSelector`。
- `jalium-v-tree` 生成命名 `PART_ScrollViewer` / `PART_Canvas` / `PART_GridDecorator` / `PART_SurfaceBorder` / `PART_MinimapOverlay` 的 `UserControl`，并把表面的 `CanvasTransform` 重新暴露为 CLR 属性，因为 Jalium 绑定无法寻址附加属性。

## 类：`WorkflowEvents`（WPF / WinUI / Avalonia / MAUI / Jalium）

把组件的模型事件绑到宿主对象上，而不必为每个事件写一个附加属性。源码：`Src/Adapters/<Adapter>/Attached/Workflow/WorkflowEvents.cs`。

| 附加属性 | 类型 | 转发者 |
|---|---|---|
| `Node` | `IWorkflowNodeEventSink?` | `WorkflowEventRelay` |
| `Slot` | `IWorkflowSlotEventSink?` | `WorkflowEventRelay` |
| `Tree` | `IWorkflowTreeEventSink?` | `WorkflowEventRelay` |

各有常见的 `Get*` / `Set*` 访问器。把它挂在 `DataContext` 是组件的那个视图上：订阅跟随数据上下文，因此池化视图被交给另一个节点时会先摘掉旧订阅再建新订阅。

## 类：`WorkflowBindingExtensions`（WinForms）

WinForms 视图的静态订阅辅助（`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowBindingExtensions.cs`）。每个都返回一个 `IDisposable`，控件释放时也会自动结束。

| 方法 | 签名 |
|---|---|
| `Bind` | `static IDisposable Bind<TModel>(this Control control, TModel? model, Action<Control, TModel> apply)` |
| `Bind`（投影） | `static IDisposable Bind<TModel, TValue>(this Control control, TModel? model, Func<TModel, TValue> selector, Action<Control, TValue> apply)` |
| `BindCollection` | `static IDisposable BindCollection(this Control control, INotifyCollectionChanged? source, Action<Control, NotifyCollectionChangedEventArgs> onChange)` |

返回的订阅会编组到控件线程，并在 `Control.Disposed` 时解除。

## WinForms 各角色附加类

WinForms 没有节点/槽/连线三种视图的基类；生成的视图各自对自己调用 `Attach(Control)`，控件仍由宿主绘制。三者都位于 `VeloxDev.WorkflowSystem.AttachedBehaviors`，都是 sealed，并用 `ConditionalWeakTable` 保证**每个控件一个实例** —— `Attach` 幂等，`For` 返回已有实例。

### 类：`WorkflowNodeAttachment`

`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowNodeAttachment.cs`；实现 `IWorkflowSurfaceNodeView`。

**静态方法**

| 方法 | 签名 |
|---|---|
| `Attach` | `static WorkflowNodeAttachment Attach(Control target)` —— `null` 抛 `ArgumentNullException` |
| `For` | `static WorkflowNodeAttachment? For(Control target)` |
| `DisposeChildren` | `static void DisposeChildren(Control parent)` |
| `ParseColor` | `static Color ParseColor(string hex)` |

**属性**

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | get/set | 绑定的节点；赋值会重绑事件并重新摆放卡片。 |
| `Title` | `string` | get | 经 `NodeTitle` 读出的标题。 |
| `Collapse` | `double` | get | `1 / Scale`（缩放为 1 时是 1）。 |
| `SurfaceBackdrop` | `Color` | get/set | 卡片擦除用的不透明底色。 |
| `SurfacePanOffset` | `Point` | get | 表面最后一次交给它的平移量。 |
| `SurfaceContentOffset` | `Offset` | get | 表面最后一次交给它的世界原点。 |
| `NodeTitle` | `Func<IWorkflowNodeViewModel, string>?` | get/set | 视图如何读取节点标题。 |
| `SlotLabel` | `Func<IWorkflowSlotViewModel, string?>?` | get/set | 视图如何读取槽自身的标签。 |

**方法**

| 方法 | 签名 | 说明 |
|---|---|---|
| `ApplySurfacePosition` | `void ApplySurfacePosition(Point panOffset, Offset contentOffset)` | 记录表面投影并重新摆放卡片。 |
| `ApplyPosition` | `void ApplyPosition()` | 按 `Anchor + pan + content` 摆放、按 `Size` 调整尺寸，并触发 `CollapseChanged` / `Repositioned`。 |
| `ResolveInputSlot` | `IWorkflowSlotViewModel? ResolveInputSlot()` | 找出节点的固定输入口（只能作源、不能作目标）。 |
| `ResolveSlotLabel` | `string ResolveSlotLabel(IWorkflowSlotViewModel slot, int index)` | 枚举器名称 → `SlotLabel` → `"Output {n}"`。 |

**事件**

| 事件 | 类型 | 触发时机 |
|---|---|---|
| `Repositioned` | `EventHandler?` | 卡片已重新摆放。 |
| `Rebound` | `EventHandler?` | 节点或其 `Slots` 集合变化。 |
| `TitleChanged` | `EventHandler?` | 节点标题变化。 |
| `CollapseChanged` | `EventHandler<CollapseChangedEventArgs>?` | 缩放的折叠因子变化（`CollapseChangedEventArgs.Collapse`）。 |
| `Moving` / `Moved` | `EventHandler<NodeMoveEventArgs>?` | 节点移动前 / 后（`Moving` 可 `PreventDefault`）。 |
| `Resizing` / `Resized` | `EventHandler<NodeResizeEventArgs>?` | 节点调整尺寸前 / 后（`Resizing` 可 `PreventDefault`）。 |
| `Deleting` / `Deleted` | `EventHandler<NodeEventArgs>?` | 节点移除前 / 后（`Deleting` 可 `PreventDefault`）。 |
| `AnchorChanged` | `Action?` | 重新摆放后锚点或尺寸变化（小地图据此重绘）。 |

### 类：`WorkflowSlotAttachment`

`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowSlotAttachment.cs`。

**静态方法**

| 方法 | 签名 |
|---|---|
| `Attach` | `static WorkflowSlotAttachment Attach(Control target)` —— `null` 抛 `ArgumentNullException` |
| `For` | `static WorkflowSlotAttachment? For(Control target)` |
| `ParseColor` | `static Color ParseColor(string hex)` |
| `Opaque` | `static Color Opaque(Color color)` —— 把 alpha 强制为 255 |

**属性**

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `Slot` | `IWorkflowSlotViewModel?` | get/set | 绑定的槽；赋值会重绑事件与可见性。 |
| `SlotPath` | `string` | get/set | 以 `PathViewBox` 画板坐标表示的 SVG 路径字形。 |
| `PathViewBox` | `float` | get/set | 画板尺寸（默认 `1024`）；非正值被忽略。 |
| `SlotBackground` | `Color` | get/set | 控件没有父控件时的兜底底色。 |
| `StandbyColor` | `Color` | get/set | 空闲状态下的字形填充。 |
| `BorderColor` | `Color` | get/set | 字形描边。 |
| `IconPath` | `GraphicsPath?` | get | 解析后的字形；`SlotPath` 未设置时为 `null`。 |
| `GlyphColor` | `Color` | get | sender+receiver 为 `Violet`，sender 为 `Tomato`，receiver 为 `Lime`，否则 `StandbyColor`。 |

**方法**

| 方法 | 签名 | 说明 |
|---|---|---|
| `Paint` | `void Paint(Graphics g)` | 把 `IconPath` 从 `PathViewBox` 缩放进控件，用 `GlyphColor` + `BorderColor` 绘制。`Graphics` 为 `null` 抛 `ArgumentNullException`。 |

**事件**

| 事件 | 类型 | 触发时机 |
|---|---|---|
| `ChannelChanging` | `EventHandler<SlotChannelEventArgs>?` | 槽的通道变化前（`PreventDefault` 可保持原值）。 |
| `ChannelChanged` | `EventHandler<SlotChannelEventArgs>?` | 槽的通道变化后。 |

构造函数还会调用 `WorkflowSlotConnectionBehavior.SetIsEnabled(control, true)`，因此挂上附加类的槽无需额外接线就参与拖拽连线手势。

### 类：`WorkflowLinkAttachment`

`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowLinkAttachment.cs`。

**静态方法**

| 方法 | 签名 |
|---|---|
| `Attach` | `static WorkflowLinkAttachment Attach(Control target)` —— `null` 抛 `ArgumentNullException` |
| `For` | `static WorkflowLinkAttachment? For(Control target)` |
| `ParseColor` | `static Color ParseColor(string hex)` |

**属性**

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `Link` | `IWorkflowLinkViewModel?` | get | 当前绑定的连线。 |
| `Curve` | `PointF[]?` | get | 控件局部坐标下的四个贝塞尔点；无可绘制内容时为 `null`。 |
| `LineColor` | `Color` | get/set | 描边颜色。 |
| `Thickness` | `float` | get/set | 描边宽度；非正值被忽略，并重新雕琢窗口区域。 |
| `PullMinimum` | `float` | get/set | 控制点最小水平拉力；负值被忽略。 |
| `SurfaceBackground` | `Color` | get/set | 连线背后的颜色；应与表面网格底色一致。 |

**方法**

| 方法 | 签名 | 说明 |
|---|---|---|
| `Bind` | `void Bind(IWorkflowLinkViewModel? link)` | 绑定 / 回收控件：撤销旧曲线、迁移输入订阅、订阅连线与两端、重建几何。 |
| `Sync` | `void Sync(IWorkflowLinkViewModel? link)` | 重读 `IsVisible` 并重建几何。 |
| `ApplySurfacePosition` | `void ApplySurfacePosition(Point panOffset, Offset contentOffset)` | 记录表面投影并重建几何。 |
| `Paint` | `void Paint(Graphics g)` | 绘制静息三次曲线（虚拟连线为虚线）。`Graphics` 为 `null` 抛 `ArgumentNullException`。 |

**事件**（来自连线的 `IInputEvents`）

| 事件 | 类型 |
|---|---|
| `PointerEntered` | `EventHandler<PointerEnteredEventArgs>?` |
| `PointerLeft` | `EventHandler<PointerExitedEventArgs>?` |
| `PointerPressed` | `EventHandler<PointerPressedEventArgs>?` |
| `PointerReleased` | `EventHandler<PointerReleasedEventArgs>?` |
| `KeyDown` / `KeyUp` | `EventHandler<KeyDownEventArgs>?` / `EventHandler<KeyUpEventArgs>?` |

事件参数类型位于 `VeloxDev.WorkflowSystem`；源码把该命名空间别名为 `Wf`。

`Attach` 会把控件设为 `Enabled = false`、`TabStop = false`，并把窗口区域雕成描边带，因此连线不会吞掉画布手势。每次重建几何时，`Bind` / `RebuildGeometry` 都通过 `link.PublishCurve(...)` 发布曲线，使命中测试与绘制共用同一条曲线。

## 接口：`IWorkflowTemplateSelector`（WinForms）

附加行为命名空间里的模板选择工厂，声明于 `Src/Adapters/VeloxDev.WinForms/Attached/Workflow/ViewManager.cs`，由生成的 `WorkflowTemplateSelector` 实现。Jalium 改用平台 `DataTemplateSelector`。

| 适配器 | 成员 |
|---|---|
| WinForms | `Control CreateView(object item)` |

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

### `WorkflowPresentation`

Razor 视图使用的静态 CSS / 几何辅助：`MinorGridColor`、`RulerBackground`、`RulerTickColor`、`RulerDividerColor`、`NodeForegroundCss`（CSS 字符串），`ToCss(string)`，以及 `InputSlotsOf(node)` / `OutputSlotsOf(node)` / `SlotNamesOf(node)`（按通道拆分槽并生成标签）。

### `SurfacePointerKind`

Razor 表面接受的浏览器级指针类型 —— `Entered`、`Moved`、`Exited`、`Pressed`、`Released`、`Wheel` —— `WorkflowSurfaceBehavior.RoutePointerAsync` 在共享输入路由看到它们之前把其映射为 Core 的 `PointerEventArgs`。
