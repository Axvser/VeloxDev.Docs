# 表面与视图池

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 类：WorkflowSurfaceBehavior

`public partial class WorkflowSurfaceBehavior : ComponentBase, IAsyncDisposable`

XAML 表面附着行为的 Blazor 对应物。它渲染滚动容器、画布、网格层、窗格与连线菜单外壳，并把指针、滚轮与按键输入路由进 `WorkflowInput`。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Tree` | `ITreeComponent?` | `null` | 表面渲染的工作流树。 |
| `IsEnabled` | `bool` | `false` | 启用平移与滚动跟踪，并加载 JS 模块。 |
| `ZoomEnabled` | `bool` | `false` | 通过 JS 接上 Ctrl+滚轮缩放。 |
| `ScrollViewerId` | `string` | `"veloxdev-wf-scroll"` | 滚动容器元素 id。 |
| `CanvasId` | `string` | `"veloxdev-wf-canvas"` | 画布元素 id。 |
| `GridDecorator` | `RenderFragment<SurfaceViewport>?` | `null` | 可选标尺/网格片段，接收视口。 |
| `Minimap` | `RenderFragment<SurfaceViewport>?` | `null` | 可选小地图片段，接收视口。 |
| `ChildContent` | `RenderFragment<SurfaceCanvas>?` | `null` | 画布内容；接收计算出的画布尺寸。 |
| `LinkMenu` | `RenderFragment<ILinkComponent>?` | `null` | 菜单条目；片段接收被右击的连线。 |
| `Background` | `string` | `"#0B1120"` | 画布背景色。 |
| `GridColor` | `string` | `"#2A2D2E"` | 次网格线颜色。 |
| `GridSpacing` | `double` | `40` | 网格间距（像素）。 |
| `MajorGridColor` | `string` | `"#3A3D40"` | 主网格线颜色。 |
| `MajorLineEvery` | `int` | `5` | 主网格线之间的次格数。 |
| `AxisColor` | `string` | `"#4D4D4D"` | 世界原点轴线颜色。 |
| `RulerThickness` | `double` | `28` | 为装饰器预留的标尺带。 |

### 属性

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `MenuLink` | `ILinkComponent?`（get） | 当前打开的右键菜单所作用的连线，或 `null`。 |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `RoutePointerAsync(SurfacePointerKind kind, double clientX, double clientY, MouseButton button = MouseButton.None, double deltaY = 0, IWorkflowComponent? target = null, InputModifiers modifiers = InputModifiers.None)` | `Task` | 把视口坐标换成画布局部坐标并路由一次指针事件。 |
| `RequestPressVerdict(double localX, double localY, int button, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`；返回订阅者是否否决了这次按下。 |
| `RequestWheelVerdict(double localX, double localY, double deltaY, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`；JS 缩放前先判定 Ctrl+滚轮。 |
| `RequestWheelScroll(double localX, double localY, double deltaX, double deltaY, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`；路由普通滚轮，未被否决时补上默认滚动。 |
| `OnHoverTarget(string? id)` | `void` | `[JSInvokable]`；记录悬停的节点/插槽 id。 |
| `OnWheelZoom(int wheelDelta, double scrollX, double scrollY, double viewportW, double viewportH, double reachW, double reachH)` | `Task` | `[JSInvokable]`；把连发缩放合并成一次原子应用。 |
| `OnSurfaceScroll(double scrollLeft, double scrollTop, double viewportW, double viewportH, double canvasW, double canvasH, double offsetX, double offsetY)` | `void` | `[JSInvokable]`；记录滚动、扩展画布并发布视口。 |
| `DisposeAsync()` | `ValueTask` | 释放模型订阅与 JS 句柄。 |

公开方法都不声明异常。`RoutePointerAsync` 内部的互操作失败会被吞掉，事件直接丢弃。

### 示例

```razor
<div style="position:relative;width:100vw;height:100vh;">
    <TreeView Tree="_tree" />
</div>
```

```razor
<LinkMenu Context="link">
    <button type="button" @onclick="() => link.DeleteCommand.Execute(null)">Delete</button>
</LinkMenu>
```

### 备注

- 表面需要一有真实高度的父元素。`100vh` 给滚动元素一个视口；`height:auto` 会把它塌成零，画布量到零。
- 普通滚轮归 JS，因为它需要同步的 `preventDefault`；默认滚动由表面在 `RequestWheelScroll` 里补。
- 连线菜单打开期间，`WorkflowInput.IsSuspended` 保留指针目标，指针移到菜单上不会把它清掉。
- 悬停连线时焦点会以 `preventScroll` 移到表面根，Delete 因此能进输入路由。

## 类：ViewPool

`public partial class ViewPool : ComponentBase, IDisposable`

Blazor 原生视图池：渲染器自己负责组件实例化与 diff，所以本组件只是源与逐项片段之上的薄包装。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `ItemsSource` | `IEnumerable?` | `null` | 要渲染的项；实现 `INotifyCollectionChanged` 时变化会重渲染。 |
| `ItemTemplate` | `RenderFragment<object>?` | `null` | 逐项片段；项是片段上下文。 |
| `EmptyContent` | `RenderFragment?` | `null` | 源为空时渲染。 |
| `KeySelector` | `Func<object, object>?` | `null` | 稳定重渲染的键（`@key` 的对应物）。 |

### 方法

`public void Dispose()` 摘掉集合变化处理器。

### 备注

- 一次虚拟化扫描会连发许多 Add/Remove；视图池把它们合并成每个渲染回合一次快照、一次 `StateHasChanged`。
- 通过 `KeySelector` 的键控渲染是保留逐项组件状态的方式。
