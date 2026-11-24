# 命中测试与几何

适配器用各自的平台图元画连线，但命中测试必须跨平台一致。`LinkCurve` 是视图发布的展平几何；`LinkHitTestEx` 与 `SlotHitTestEx` 在画布坐标里消费它。

## LinkCurve

```csharp
public sealed class LinkCurve
```

由三次曲线采样得到的不可变折线，带弧长索引。构造函数是私有的；用工厂方法创建。

### 属性与常量

| 成员 | 类型 | 说明 |
|---|---|---|
| `DefaultSampleCount` | `const int` | `128`；所有构建器的默认采样数。 |
| `Count` | `int` | 采样点数量。 |
| `Bounds` | `WorkflowBounds` | 采样点的包围盒。 |
| `Length` | `double` | 总弧长。 |

### 点访问

| 签名 | 返回 | 说明 |
|---|---|---|
| `XAt(int index)` | `double` | 某个采样点的 X。不做边界检查。 |
| `YAt(int index)` | `double` | 某个采样点的 Y。不做边界检查。 |
| `LengthAt(int index)` | `double` | 某个采样点处的累计弧长。不做边界检查。 |
| `PointAtLength(double length)` | `(double X, double Y)` | 按弧长插值，钳制在 `[0, Length]`。 |

### 工厂

| 签名 | 说明 |
|---|---|
| `static FromPoints(IReadOnlyList<double> xs, IReadOnlyList<double> ys)` | 从两组对应坐标构建。列表为 null 时抛 `ArgumentNullException`，长度不一致时抛 `ArgumentException`。 |
| `static BuildCubic(double startX, double startY, double endX, double endY, double pullMinimum, int sampleCount = DefaultSampleCount)` | 水平三次曲线；拉伸量为 `max(pullMinimum, |Δx| / 2)`。采样数非正时回退到 128。 |
| `static FromCubic(double p0X, double p0Y, double p1X, double p1Y, double p2X, double p2Y, double p3X, double p3Y, int sampleCount = DefaultSampleCount)` | 对显式三次曲线采样。 |
| `static LinkCurvePoints(ILinkComponent? link, double startX, double startY, double endX, double endY, double pullMinimum)` | 沿每个端口外法线返回控制点序列；某一端没有节点时回退到水平规则。 |
| `static BuildLinkCubic(ILinkComponent? link, double startX, double startY, double endX, double endY, double pullMinimum, int sampleCount = DefaultSampleCount)` | 对考虑端口方向的曲线采样。 |
| `static PortOutward(ISlotComponent slot)` | 插槽的外法线。插槽为 null 时抛 `ArgumentNullException`。 |
| `static PortOutward(double x, double y, INodeComponent? node)` | 点相对节点的外法线；没有节点或节点尺寸为零时返回 `(0,0)`。 |

### 命中

| 签名 | 返回 | 说明 |
|---|---|---|
| `Contains(double x, double y, double radius)` | `bool` | 点是否在折线 `radius` 范围内。 |

## ILinkHitTestable

```csharp
public interface ILinkHitTestable
{
    object? Visual { get; }
    LinkCurve? Curve { get; }
    void SetCurve(LinkCurve? curve, object? visual = null);
    bool Contains(double x, double y, double radius);
}
```

扩展方法背后的逐连线存储。曲线是引用而不是副本；发布 `null` 即撤回。

## LinkHitTestEx

```csharp
public static class LinkHitTestEx
{
    public const double DefaultHitRadius = 6d;

    public static ILinkHitTestable? HitTarget(this ILinkComponent link);
    public static void PublishCurve(this ILinkComponent link, LinkCurve? curve, object? visual = null);
    public static bool HitTest(this ILinkComponent link, double x, double y, double radius = DefaultHitRadius);
    public static ILinkComponent? HitTestVisibleLinks(this ITreeComponent tree, double x, double y, double radius = DefaultHitRadius);
}
```

| 成员 | 行为 |
|---|---|
| `DefaultHitRadius` | 6 个画布单位；半径不随缩放变化。 |
| `HitTarget` | 返回连线的曲线存储，首次访问时创建。 |
| `PublishCurve` | 保存视图画出的曲线与一个可选视图引用。 |
| `HitTest` | 要求 `link.IsVisible` 且已发布曲线。 |
| `HitTestVisibleLinks` | 从后往前遍历 `tree.GetHelper().VisibleItems`，跳过虚拟连线，也跳过被节点覆盖的点。 |

`HitTestVisibleLinks` 是连线右键菜单的标准路径。没有发布曲线的连线永远不会被命中。

## SlotHitTestEx

```csharp
public static class SlotHitTestEx
{
    public const double DefaultHitRadius = 12d;

    public static ISlotComponent? HitTest(ITreeComponent tree, double x, double y, double radius = DefaultHitRadius);
}
```

找出画布点 `radius` 范围内最近的插槽。与连线助手不同，这是静态方法而非扩展。跳过锚点为 NaN 的插槽，返回最近匹配；树为 null 时抛 `ArgumentNullException`。默认半径是 12 个画布单位。

## 说明

- 所有坐标都是画布局部坐标，与 `Anchor.Horizontal` 和 `Anchor.Vertical` 同一空间。
- `LinkCurve.BuildLinkCubic` 用发送端与接收端插槽确定手柄方向；`BuildCubic` 忽略连线，是回退方案。
- 发布新曲线会替换旧曲线。连线端点移动后，适配器必须重新绘制并重新发布。
