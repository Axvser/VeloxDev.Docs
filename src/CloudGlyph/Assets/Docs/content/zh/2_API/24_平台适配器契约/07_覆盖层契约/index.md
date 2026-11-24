# 覆盖层契约

两个数据交换接口让表面把同一组数字推给网格装饰器和小地图，而无需知道它们如何绘制。XAML 适配器不附带装饰器；宿主按此接口自己写一个，或从条目模板生成。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## IWorkflowGridDecorator

**签名：** `interface IWorkflowGridDecorator`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double`（get/set） | 表面滚动容器的偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double`（get/set） | 画布内容偏移。 |
| `RulerBand` | `double`（get） | 覆盖上/左边缘的浮动标尺带厚度；没有时为 `0`。 |

表面在每次刷新前写入四个偏移。`RulerBand` 每次刷新被读取，并转发给 `ITreeComponent.SetVirtualizeInset(left: RulerBand, top: RulerBand)`，使浮动标尺下方的节点不被剔除。

## IWorkflowMinimapOverlay

**签名：** `interface IWorkflowMinimapOverlay : IWorkflowGridDecorator`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ViewportWidth` / `ViewportHeight` | `double`（get/set） | 与推送偏移同一滚动空间的视口尺寸。 |
| `WorkflowTree` | `ITreeComponent?`（get/set） | 小地图渲染的树。 |
| `IsMinimapVisible` | `bool`（get/set） | 覆盖层是否应渲染。 |
| `AvailableRight` | `double`（get/set） | 内容视口右边缘的局部像素坐标，不含垂直滚动条。 |
| `AvailableTop` | `double`（get/set） | 上边缘，在水平标尺带之下。 |
| `AvailableBottom` | `double`（get/set） | 下边缘，在水平滚动条之上。 |
| `MinimapMargin` | `double`（get/set） | 小地图与可用角的间距。 |

表面每次刷新通过 `SurfaceMetricsPush.PushMinimap` 推送全部成员。小地图绘制缩略图与视口框，并把拖拽解析回滚动偏移。

```csharp
public sealed class GridDecorator : Grid, IWorkflowGridDecorator
{
    public double ScrollOffsetX { get; set; }
    public double ScrollOffsetY { get; set; }
    public double ContentOffsetX { get; set; }
    public double ContentOffsetY { get; set; }
    public double RulerBand => 0d;
}
```

**预期结果：** 滚动后，装饰器的 `ScrollOffsetX` 与 `tree.GetHelper().Viewport.Horizontal` 一起移动；覆盖上/左边缘的装饰器必须从 `RulerBand` 返回该厚度。
