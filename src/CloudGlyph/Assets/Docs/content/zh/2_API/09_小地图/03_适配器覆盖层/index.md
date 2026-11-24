# 适配器覆盖层

WPF 小地图是一个 `FrameworkElement` 覆盖层加三个小的平台类。覆盖层暴露放置与画刷的依赖属性；拖动与绘制由管线处理。

命名空间：覆盖层在 `VeloxDev.WorkflowSystem.AttachedBehaviors`；管线类在 `VeloxDev.WorkflowSystem.ViewHosting`。

## WorkflowMinimapOverlay

```csharp
public class WorkflowMinimapOverlay : FrameworkElement, IWorkflowMinimapOverlay
```

### 放置与状态属性

| 属性 | 类型 | 默认 | 含义 |
|---|---|---:|---|
| `WorkflowTree` | `ITreeComponent?` | `null` | 要渲染的树。 |
| `ViewportWidth` / `ViewportHeight` | `double` | `1d` | 滚动空间中的视口尺寸。 |
| `IsMinimapVisible` | `bool` | `true` | 一次绘制是否画出。 |
| `MinimapWidth` / `MinimapHeight` | `double` | `200d` / `140d` | 请求尺寸。 |
| `MinimapMargin` | `double` | `12d` | 与角的间距。 |
| `MinimapMinSize` | `double` | `20d` | 最小边长。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0d` | 表面推送的角边缘。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0d` | 表面推送的滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0d` | 表面推送的内容偏移。 |
| `RulerThickness` | `double` | `28d` | 报告给表面的标尺厚度。 |
| `ScrollViewerName` | `string?` | `null` | 拖动要写回的滚动视图。 |

### 外观属性

| 属性 | 类型 | 默认 |
|---|---|---|
| `MinimapBackground` | `Brush?` | `#331E1E1E` |
| `MinimapBorderBrush` | `Brush?` | `#DC94A3B8` |
| `NodeBrush` | `Brush?` | `#DC38BDF8` |
| `LinkBrush` | `Brush?` | `#B4B4C8DC` |
| `ViewportFill` | `Brush?` | `#28FFFFFF` |
| `ViewportStroke` | `Brush?` | `#F0FFFFFF` |
| `MinimapBorderThickness` | `double` | `1.0` |
| `ViewportStrokeThickness` | `double` | `1.5` |
| `LinkStrokeThickness` | `double` | `2.0` |
| `MinimapCornerRadius` | `double` | `4.0` |
| `NodeCornerRadius` | `double` | `1.0` |
| `ContentPadding` | `double` | `2.0` |

### 接口成员

| 成员 | 说明 |
|---|---|
| `RulerBand` | 恒为 `0`；WPF 覆盖层不绘制单独的标尺带。 |

### 受保护的绘制钩子

```csharp
protected virtual void DrawMinimap(DrawingContext dc, MinimapDrawContext context);
```

重写并调用 `base` 可在默认边框、缩略块与视口块上追加；完全替换则画自己的内容。`LinkBrush` 与 `LinkStrokeThickness` 虽已声明，默认绘制不画连线；`MinimapDrawContext` 只带节点与视口矩形。

构造函数把 `IsHitTestVisible` 与 `Focusable` 设为 `true`，加载时解析 `ScrollViewerName`，卸载时丢弃管线的树。

## MinimapPipeline

```csharp
public sealed class MinimapPipeline
    : MinimapPipelineCore<DrawingContext, IMinimapRenderer<DrawingContext>,
        IMinimapViewportHost, IMinimapInputHost>
```

泛型管线的 WPF 闭合。构造函数参数与基类相同：渲染器、视口宿主、输入宿主与可选 metrics。

## MinimapRenderer

```csharp
public sealed class MinimapRenderer : IMinimapRenderer<DrawingContext>
```

| 成员 | 说明 |
|---|---|
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | owner 为 null 时抛 `ArgumentNullException`。 |
| `Render(DrawingContext surface, MinimapDrawContext context)` | 转发到 owner 的受保护 `DrawMinimap`。 |

## MinimapViewportHost

```csharp
public sealed class MinimapViewportHost : IMinimapViewportHost
```

| 构造函数 / 成员 | 说明 |
|---|---|
| `MinimapViewportHost(ScrollViewer scrollViewer)` | 直接读写并滚动该视图的独立宿主。为 null 时抛 `ArgumentNullException`。 |
| `ScrollOffsetX` / `ScrollOffsetY` | 有 owner 时用覆盖层推送值，否则用视图偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | 覆盖层推送的内容偏移。 |
| `ViewportWidth` / `ViewportHeight` | 覆盖层推送的视口尺寸，否则用视图的。 |
| `ScrollableWidth` / `ScrollableHeight` | 视图的可滚动范围。 |
| `ApplyScroll(double x, double y)` | 调用 `ScrollToHorizontalOffset` 与 `ScrollToVerticalOffset`。 |

## MinimapInputHost

```csharp
public sealed class MinimapInputHost : IMinimapInputHost
```

| 成员 | 说明 |
|---|---|
| `MinimapInputHost()` | 用于测试或自定义表面的独立宿主。 |
| `PointerPosition` | 覆盖层局部指针位置；公开 setter。 |
| `IsPressed` | 主键是否按下；公开 setter。 |
| `IsCaptured` | 是否持有捕获；私有 setter。 |
| `ClampRect` | 可选命中矩形；公开 setter。 |
| `Capture()` | 捕获 owner 的鼠标；返回是否成功。 |
| `Release()` | 释放捕获。 |

## 说明

- 表面行为必须解析 `MinimapOverlayName`；否则覆盖层没有树，什么也不画。
- 覆盖层自己的 `ScrollViewerName` 让拖动能把偏移写回；它与表面自己的 `ScrollViewerName` 是两回事。
- 宿主通常继承覆盖层，在构造函数里改颜色或重写 `DrawMinimap`；不需要碰其他成员。
