# 表面导航

导航是挂载表面注册到树的输入路由上的可选能力。Core 提供契约、一个面向窄宿主的实现，以及只依赖模型数据的 `Locate()` 扩展。

## IWorkflowSurfaceScroller

```csharp
public interface IWorkflowSurfaceScroller
{
    void ScrollBy(double wheelDeltaX, double wheelDeltaY);
}
```

以滚轮事件的增量调用。水平正方向是「右」，垂直正方向是「远离用户」；实现会在垂直轴上做减法。某个轴为 0 时该轴不动。

## IWorkflowSurfaceNavigator

```csharp
public interface IWorkflowSurfaceNavigator
{
    void CenterOn(double localX, double localY);
}
```

把画布局部点放到视口中心。缩放不变。

## ISurfaceScrollHost

```csharp
public interface ISurfaceScrollHost
{
    CanvasLayout? Layout { get; }
    double ViewportWidth { get; }
    double ViewportHeight { get; }
    double HorizontalOffset { get; }
    double VerticalOffset { get; }
    double HorizontalMaximum { get; }
    double VerticalMaximum { get; }
    SurfaceWheelProfile WheelProfile { get; }
    void ApplyOffset(double? horizontalOffset, double? verticalOffset);
    void ExpandCanvas();
}
```

适配器的窄接缝。`Layout` 可以为 `null`，此时 scroller 只做钳制，不扩展画布。`ApplyOffset` 的某个参数为 `null` 时该轴不动。

## SurfaceWheelProfile

```csharp
public readonly struct SurfaceWheelProfile
{
    public double DeltaPerNotch { get; init; }
    public double PixelsPerNotch { get; init; }
    public double ScrollLines { get; init; }
    public double LineHeight { get; init; }

    public static SurfaceWheelProfile FromLines(
        double deltaPerNotch, double scrollLines,
        double lineHeight = SurfaceScrollerCore.DefaultLineHeight);
    public static SurfaceWheelProfile FromPixels(double deltaPerNotch, double pixelsPerNotch);
}
```

| 成员 | 含义 |
|---|---|
| `DeltaPerNotch` | 一格滚轮的原始增量；必须为正，否则实现按 1 处理。 |
| `PixelsPerNotch` | 每格像素数；`0` 表示改用行步进模式。 |
| `ScrollLines` | 每格行数；非正数表示一整个视口。 |
| `LineHeight` | 行步进模式下每行像素数。 |

`FromLines` 配置平台自己的步进。`FromPixels` 配置固定像素步进。

## SurfaceScrollerCore

```csharp
public sealed class SurfaceScrollerCore : IWorkflowSurfaceScroller, IWorkflowSurfaceNavigator
```

两个契约的 Core 实现，面向 `ISurfaceScrollHost` 编写。

### 常量

| 常量 | 值 | 含义 |
|---|---:|---|
| `DefaultWheelDelta` | `120d` | 一格的原始滚轮单位。 |
| `DefaultLineHeight` | `16d` | 配置按行步进时每行的像素数。 |

### 方法

| 签名 | 说明 |
|---|---|
| `SurfaceScrollerCore(ISurfaceScrollHost host)` | `host` 为 null 时抛 `ArgumentNullException`。 |
| `ScrollBy(double wheelDeltaX, double wheelDeltaY)` | 按宿主的配置转换增量、钳制，并在越界时按 `WorkflowSurfaceMath.DefaultPanExtendRatio`（0.15）扩展画布。`(0,0)` 增量是空操作。 |
| `CenterOn(double localX, double localY)` | 用 `WorkflowSurfaceMath.CenterScroll` 计算，点无法居中时按精确差值扩展画布，重新读取最大值后应用钳制后的偏移。`Layout` 为 null 时是空操作。 |

`ScrollBy` 在 Y 轴上做减法，因为滚轮正增量表示「远离用户」，而正偏移表示「向下」。调用方把一根轴映射到另一根轴时需自行翻转符号。

## WorkflowNavigationEx

```csharp
namespace VeloxDev.WorkflowSystem.StandardEx;

public static class WorkflowNavigationEx
{
    public static bool Locate(this INodeComponent node);
    public static bool Locate(this ISlotComponent slot);
    public static bool Locate(this ILinkComponent link);
}
```

`Locate()` 只读模型数据，所以屏幕外的节点或尚未测量的插槽在拥有视图之前就能被居中。

| 重载 | 居中的点 |
|---|---|
| `Locate(INodeComponent)` | 节点矩形的中心。 |
| `Locate(ISlotComponent)` | 父节点矩形的中心；不读取插槽自己的 `Anchor`。 |
| `Locate(ILinkComponent)` | 两端节点中心连线的中点；不读取已发布的曲线。 |

没有注册 `IWorkflowSurfaceNavigator` 或目标没有有限位置时，返回 `false` 且什么也不改。参数为 null 时抛 `ArgumentNullException`。缩放保持不变。

## 说明

- 两项能力在挂载表面注册前都是 `null`，表面卸载时被清空。当作可选项处理。
- scroller 选择扩展画布而不是在边缘停住。宿主接受新范围后会重新读取最大值。
- 适配器通常注册同一个 `SurfaceScrollerCore` 同时填两个槽位。
