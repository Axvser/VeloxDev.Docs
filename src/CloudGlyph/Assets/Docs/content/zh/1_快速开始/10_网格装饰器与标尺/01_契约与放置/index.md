# 契约与放置

表面行为不知道网格怎么画。它只知道一个接口与一个名字：由 `GridDecoratorName` 命名的元素必须实现 `IWorkflowGridDecorator`，行为把当前偏移推进去。

## 契约

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
| `ScrollOffsetX` / `ScrollOffsetY` | 表面 `ScrollViewer` 的偏移，在滚动空间里。 |
| `ContentOffsetX` / `ContentOffsetY` | `CanvasLayout.ActualOffset`，画布自己的平移。 |
| `RulerBand` | 覆盖在内容上/左边缘的浮动带厚度；没有带时为 `0`。 |

偏移由 `SurfaceMetricsPush.PushGrid` 在每次滚动、平移、缩放时写入。装饰器不订阅任何东西；属性变化时它让自己的视觉失效。

## 放置

装饰器是滚动容器的**父级**：

```xml
<Border x:Name="PART_SurfaceBorder">
    <local:GridRulerDecorator x:Name="PART_GridDecorator">
        <ScrollViewer x:Name="PART_ScrollViewer"
                      HorizontalScrollBarVisibility="Auto"
                      VerticalScrollBarVisibility="Auto">
            <Canvas x:Name="PART_Canvas"
                    Width="{Binding Layout.ActualSize.Width}"
                    Height="{Binding Layout.ActualSize.Height}">
                <Canvas.RenderTransform>
                    <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                        Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                </Canvas.RenderTransform>
            </Canvas>
        </ScrollViewer>
    </local:GridRulerDecorator>
</Border>
```

加上宿主附着属性：

```xml
behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
```

两条放置规则很重要：

1. **装饰器包住内容，不在画布里面。** 它必须按视口尺寸绘制并看到滚动偏移，只有 `ScrollViewer` 之上的宿主做得到。
2. **画布按 `RulerThickness` 平移。** 世界原点因此落在标尺带的内边缘，内容仍可滚到半透明带下面。不平移画布的话，带会盖住世界的第一行/列。

## 表面推什么

`SurfaceMetricsPush.PushGrid` 写入四个偏移，然后调用：

```csharp
tree.SetVirtualizeInset(left: decorator.RulerBand, top: decorator.RulerBand);
```

inset 放大虚拟化查询，但不移动权威的 `Viewport`。视觉上位于标尺下、但仍在视口内的节点因此得以保留。小地图读同一个值作为 `AvailableTop`，从带下方开始而不是压在上面。

`RulerBand` 在接口上是只读的：它是装饰器自身配置的函数，不是表面写入的东西。

## 预期结果

- 网格线随内容移动，并与滚动条对齐。
- 内容在标尺下方滚动时，标尺固定在顶部与左侧。
- 把节点拖到标尺带下面时，只要它还在视口内，就不会从可见集里被移除。
- 小地图的顶部落在标尺带下方，不压在它上面。

## 下一页

[绘制网格与标尺](../02_绘制网格与标尺/index.md)介绍绘制趟与四个公式。
