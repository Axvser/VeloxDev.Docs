# 滚动与导航

适配器在表面挂载期间向 `WorkflowInput` 注册的两项能力。Core 还提供一个现成实现 `SurfaceScrollerCore`，适配器通过一个小的平台宿主驱动它。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## IWorkflowSurfaceScroller

**签名：** `interface IWorkflowSurfaceScroller`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ScrollBy` | `void ScrollBy(double wheelDeltaX, double wheelDeltaY)` | 按给定增量滚动，如同滚轮转动。无法扩张表面的实现会钳制到范围；某一轴为零时该轴不动。 |

增量是**滚轮增量**，即 `PointerWheelEventArgs` 携带的值，不是滚动偏移。X 为正移向右侧内容；Y 为正移向上方内容。要让滚轮驱动另一轴，调用方自行翻转符号。

## IWorkflowSurfaceNavigator

**签名：** `interface IWorkflowSurfaceNavigator`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `CenterOn` | `void CenterOn(double localX, double localY)` | 滚动使画布局部点位于视口中心。 |

坐标与 `INodeComponent.Anchor` 和 `ITreeHelper.Viewport` 使用同一坐标系。`VeloxDev.WorkflowSystem.StandardEx` 中的 `WorkflowNavigationEx` 可从节点、插槽或连线生成该点。无法扩张表面的实现改为钳制。

## ISurfaceScrollHost

**签名：** `interface ISurfaceScrollHost`

`SurfaceScrollerCore` 驱动的平台层。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Layout` | `CanvasLayout?` | 画布几何；未绑定树时为 `null`。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 可见视口尺寸。 |
| `HorizontalOffset` / `VerticalOffset` | `double` | 当前滚动偏移。 |
| `HorizontalMaximum` / `VerticalMaximum` | `double` | 平台当前报告的最大偏移。 |
| `WheelProfile` | `SurfaceWheelProfile` | 该平台把滚轮增量换算成步长的方式。 |
| `ApplyOffset(double? horizontalOffset, double? verticalOffset)` | `void` | 写入偏移；`null` 表示该轴不动。 |
| `ExpandCanvas()` | `void` | 让平台采纳滚动器扩张后的画布。 |

## SurfaceScrollerCore

**签名：** `sealed class SurfaceScrollerCore : IWorkflowSurfaceScroller, IWorkflowSurfaceNavigator`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `DefaultWheelDelta` | `const double`（`120`） | 基于 Win32 的平台一个物理格报告的滚轮增量。 |
| `DefaultLineHeight` | `const double`（`16`） | 按行滚动时使用的行高。 |
| `SurfaceScrollerCore(ISurfaceScrollHost host)` | 构造函数 | 宿主为 null 时抛 `ArgumentNullException`。 |
| `ScrollBy(double, double)` | `void` | 通过 `host.WheelProfile` 换算滚轮增量；越过内容边缘时经 `WorkflowSurfaceMath.ClampScrollOffset` 扩张画布。 |
| `CenterOn(double, double)` | `void` | 经 `WorkflowSurfaceMath.CenterScroll` 把该点放到视口中心。 |

## SurfaceWheelProfile

**签名：** `readonly struct SurfaceWheelProfile`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `DeltaPerNotch` | `double`（init） | 一个格的原始滚轮增量。 |
| `PixelsPerNotch` | `double`（init） | 一个格滚动的像素数。 |
| `ScrollLines` | `double`（init） | 一个格滚动的行数。 |
| `LineHeight` | `double`（init） | 每行像素数。 |
| `FromLines(double deltaPerNotch, double scrollLines, double lineHeight = SurfaceScrollerCore.DefaultLineHeight)` | `static SurfaceWheelProfile` | 构建按行滚动的配置；`scrollLines` 非正表示按页滚动。 |
| `FromPixels(double deltaPerNotch, double pixelsPerNotch)` | `static SurfaceWheelProfile` | 构建按像素滚动的配置。 |

```csharp
var scroller = new SurfaceScrollerCore(myHost);
input.Scroller = scroller;
input.Navigator = scroller;

scroller.ScrollBy(0d, -120d);   // 一格，移向上方内容
scroller.CenterOn(240d, 160d);  // 把该画布点放到视口中心
```

**预期结果：** 两项能力是同一个对象；调用 `ScrollBy` 后，下一次表面刷新时宿主的偏移与 `tree.GetHelper().Viewport` 一起移动。
