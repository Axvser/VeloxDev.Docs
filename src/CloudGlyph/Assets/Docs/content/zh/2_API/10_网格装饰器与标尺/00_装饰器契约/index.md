# 装饰器契约

表面行为不知道网格怎么画。它只知道一个接口与一个名称：`GridDecoratorName` 命名的元素必须实现 `IWorkflowGridDecorator`，行为会在每次布局、滚动、平移或缩放时把当前偏移推给它。

## IWorkflowGridDecorator

```csharp
public interface IWorkflowGridDecorator
{
    double ScrollOffsetX { get; set; }
    double ScrollOffsetY { get; set; }
    double ContentOffsetX { get; set; }
    double ContentOffsetY { get; set; }
    double RulerBand { get; }
}
```

| 成员 | 含义 |
|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | 表面 `ScrollViewer` 的偏移，位于滚动空间。 |
| `ContentOffsetX` / `ContentOffsetY` | `CanvasLayout.ActualOffset`，画布自身的平移。 |
| `RulerBand` | 覆盖内容上/左边缘的浮动带厚度；没有带时为 `0`。 |

四个偏移由 `SurfaceMetricsPush.PushGrid` 写入；装饰器不订阅任何东西。`RulerBand` 在接口上只读，因为它由装饰器自身配置决定，不是表面写入的值。

## SurfaceMetrics

```csharp
public readonly struct SurfaceMetrics
```

网格消费快照中的四个成员：

| 成员 | 类型 | 用途 |
|---|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 推给装饰器的滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 推给装饰器的内容偏移。 |
| `RulerBand` | `double` | 从装饰器读出，用于构建可用角。 |
| `Available` | `SurfaceAvailableArea` | 覆盖层的可用角；`Top` 从标尺带下方开始。 |

`SurfaceMetrics` 与 `SurfaceMetrics.Create` 的完整说明见[表面数学](../../07_画布输入与导航/03_表面数学/index.md)。

## SurfaceMetricsPush.PushGrid

```csharp
public static void PushGrid(SurfaceMetrics metrics, IWorkflowGridDecorator decorator, ITreeComponent? tree);
```

1. 把 `ScrollOffsetX`、`ScrollOffsetY`、`ContentOffsetX`、`ContentOffsetY` 写进装饰器。
2. 调用 `tree.SetVirtualizeInset(left: decorator.RulerBand, top: decorator.RulerBand)`。

装饰器为 null 时抛 `ArgumentNullException`；`tree` 可以为 null。

inset 会扩张虚拟化查询，但不移动权威视口。因此视觉上位于标尺下方、实际仍在视口内的节点不会被剔除。小地图把同一个值当作 `AvailableTop`，从而从带下方开始，而不是压在带上。

## SurfaceAvailableArea

```csharp
public readonly struct SurfaceAvailableArea : IEquatable<SurfaceAvailableArea>
```

与网格相关的成员是 `Top`：`SurfaceMetrics.Create` 把它设为 `max(0, rulerBand)`，这正是把小地图及其他角落覆盖层推到标尺下方的原因。完整成员见[表面数学](../../07_画布输入与导航/03_表面数学/index.md)。

## 说明

- 画了带就必须报告真实的 `RulerBand`。画带却报告 `0`，会让标尺下的节点提前一个带宽度被剔除，并把小地图压在标尺上。
- 推送每次绘制都发生；装饰器只在值变化时让自己的视觉失效。
- 接口由绘制类实现，不由适配器实现。适配器只解析命名部件。
