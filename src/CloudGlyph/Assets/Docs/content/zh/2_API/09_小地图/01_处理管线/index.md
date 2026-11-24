# 处理管线

`MinimapPipelineCore` 订阅树的变化、把它们去抖成一次绘制、把节点与视口矩形映射进小地图，并把按下或拖动变成滚动偏移。`MinimapHostCore` 持有三个平台层。

## MinimapHostCore

```csharp
public abstract class MinimapHostCore<TSurface, TRenderer, TViewport, TInput>
    where TRenderer : class, IMinimapRenderer<TSurface>
    where TViewport : class, IMinimapViewportHost
    where TInput : class, IMinimapInputHost
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `protected MinimapHostCore(TRenderer renderer, TViewport viewport, TInput input)` | 构造函数 | 组合三个层。任一层为 null 时抛 `ArgumentNullException`。 |
| `Renderer` | `TRenderer` | 绘制一次。 |
| `Viewport` | `TViewport` | 读写滚动状态。 |
| `Input` | `TInput` | 指针状态与捕获。 |

## MinimapPipelineCore

```csharp
public class MinimapPipelineCore<TSurface, TRenderer, TViewport, TInput>
    : MinimapHostCore<TSurface, TRenderer, TViewport, TInput>, IDisposable
    where TRenderer : class, IMinimapRenderer<TSurface>
    where TViewport : class, IMinimapViewportHost
    where TInput : class, IMinimapInputHost
```

### 构造函数

| 签名 | 说明 |
|---|---|
| `MinimapPipelineCore(TRenderer renderer, TViewport viewport, TInput input, MinimapMetrics? metrics = null)` | metrics 为 `null` 表示 `MinimapMetrics.Default`。管线初始可见且为脏。 |

### 属性

| 成员 | 类型 | 说明 |
|---|---|---|
| `Metrics` | `MinimapMetrics` | 放置与样式输入。设置相等值时忽略；变化会标脏。 |
| `IsVisible` | `bool` | 一次绘制是否画出；默认 `true`。 |
| `Tree` | `ITreeComponent?` | 要渲染的树。setter 会取消订阅旧树、订阅新树并标脏。 |
| `IsDirty` | `bool` | 映射是否需要重建。 |
| `IsDragging` | `bool` | 是否正在拖动。 |
| `ContentBounds` | `WorkflowBounds` | 所有节点矩形的边界，画布局部。 |
| `ViewportBounds` | `WorkflowBounds` | 当前视口，画布局部。 |
| `DrawContext` | `MinimapDrawContext?` | 最近一次构建的绘制上下文；首次绘制前或空树时为 `null`。 |
| `SubscribedNodeCount` | `int` | 当前跟踪的节点数。 |
| `SubscribedLinkCount` | `int` | 当前跟踪的连线数。 |
| `MinimapRect` | `WorkflowBounds` | 已放置的矩形，由 `Metrics` 在右上角算出。 |

### 事件

| 事件 | 说明 |
|---|---|
| `RenderRequested` | `EventHandler`，由 `Invalidate` 触发，每次调用一次。 |

### 方法

| 签名 | 说明 |
|---|---|
| `Invalidate()` | 标脏并触发 `RenderRequested`。对已销毁实例安全。 |
| `Refresh()` | 已销毁或干净时提前返回；否则清标记并重建 `DrawContext`。 |
| `Render(TSurface surface)` | 已销毁或隐藏时返回；先刷新，再调用 `Renderer.Render(surface, DrawContext)`。渲染器在每次可见绘制时都运行，不只是脏时。 |
| `HitTest(double x, double y)` | `Input.ClampRect` 非空时判断是否在其中，否则判断是否在 `MinimapRect` 内。 |
| `PointerPressed()` | 要求按下点在小地图内；刷新、把视口居中到该点、开始拖动并捕获。返回是否开始了拖动。 |
| `PointerMoved()` | 拖动期间把视口居中到当前指针位置。 |
| `PointerReleased()` | 结束拖动并释放捕获。未拖动时是空操作。 |
| `PointerCaptureLost()` | 结束拖动并释放捕获。未拖动时是空操作。 |
| `Dispose()` | 取消订阅树并丢弃绘制上下文。 |

### 订阅规则

管线监听树节点与连线的 `INotifyCollectionChanged`。对节点监听 `Anchor` 与 `Size`；对连线监听发送端与接收端插槽的 `Anchor`。其他属性名不会标脏，因此无关属性的变化没有代价。

## MinimapDrawContext

```csharp
public sealed class MinimapDrawContext
```

按约定不可变的一次绘制。用对象初始化器创建；管线会替你构建。

| 属性 | 类型 | 说明 |
|---|---|---|
| `Tree` | `ITreeComponent?` | 要渲染的树。 |
| `ContentBounds` | `WorkflowBounds` | 所有节点的画布局部边界。 |
| `ViewportBounds` | `WorkflowBounds` | 画布局部视口。 |
| `Nodes` | `IReadOnlyList<WorkflowBounds>` | 画布局部节点矩形；默认空数组。 |
| `MappedNodes` | `IReadOnlyList<WorkflowBounds>` | 小地图局部缩略块，已加内边距并满足最小尺寸；默认空数组。 |
| `MappedViewport` | `WorkflowBounds` | 小地图局部视口指示块。 |
| `MinimapWidth` / `MinimapHeight` | `double` | 放置尺寸。 |
| `Padding` | `double` | 内边距。 |
| `OriginX` / `OriginY` | `double` | 内容在小地图内的原点。 |
| `Scale` | `double` | 内容到小地图的比例。 |
| `NodeCornerRadius` / `MinimapCornerRadius` | `double` | 圆角。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | 角边缘。 |
| `MinimapMargin` | `double` | 角间距。 |

| 成员 | 类型 | 说明 |
|---|---|---|
| `GetMinimapRect(double minimumSize)` | `WorkflowBounds` | 把请求尺寸放到可用角。 |
| `HasContent` | `bool` | `!ContentBounds.IsEmpty`。 |
| `HasViewport` | `bool` | `!ViewportBounds.IsEmpty`。 |

## 说明

- 一串属性变化只花一次重建，因为 `Invalidate` 只设置标记并触发请求。
- 映射干净时 `Render` 仍调用渲染器；平台在尺寸变化后可能需要重绘。
- 映射只读节点的 `Anchor` 与 `Size`，从不需要视图已经存在。
