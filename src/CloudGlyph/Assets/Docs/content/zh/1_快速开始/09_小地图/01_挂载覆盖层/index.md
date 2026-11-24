# 挂载覆盖层

小地图是覆盖层，不是滚动容器的子元素。它铺满表面、在可用角落自己绘制，并从表面行为那里按名字接收数据。

## 标记

```xml
<Grid>
    <Border x:Name="PART_SurfaceBorder">
        <local:WorkflowGridDecorator x:Name="PART_GridDecorator">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}" />
            </ScrollViewer>
        </local:WorkflowGridDecorator>
    </Border>

    <!-- Full-surface layer. The overlay itself draws only the 200 x 140 corner. -->
    <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                      HorizontalAlignment="Stretch"
                                      VerticalAlignment="Stretch"
                                      ScrollViewerName="PART_ScrollViewer" />
</Grid>
```

在宿主 `UserControl` 上：

```xml
behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
```

`MinimapOverlayName` 是表面推数据的开关；没有它，覆盖层没有树，什么也不画。覆盖层自己的 `ScrollViewerName` 让拖动能把滚动偏移写回去。

名字在 `UserControl` 名称作用域里解析。覆盖层必须与表面在同一个 `UserControl` 里，不能放在兄弟窗口或另一个控件的资源字典里。

## 表面推什么

每次布局/滚动经过，`SurfaceMetricsPush.PushMinimap` 写入：

| 属性 | 来源 |
|---|---|
| `ScrollOffsetX` / `ScrollOffsetY` | 滚动容器的偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `CanvasLayout.ActualOffset`。 |
| `ViewportWidth` / `ViewportHeight` | 滚动容器的视口。 |
| `WorkflowTree` | 表面的 `DataContext`。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | 可用角落：宽减去竖滚动条，顶部在标尺带之下，底部在横滚动条之上。 |
| `MinimapMargin` | 覆盖层离该角落的间隙。 |

减法在 `SurfaceMetrics.Create` 里，所以每家适配器都以同样方式缩小角落。如果网格装饰器报告了 `RulerBand`，小地图就从它下方开始。

## 放置

`MinimapPipelineCore.MinimapRect` 把请求的 `MinimapWidth` × `MinimapHeight` 放在可用角落的右上，并夹到可用区域与 `MinimapMinSize`。默认 200 × 140，最小 20，间隙 12。

如果表面的命名部件在覆盖层加载之后才出现，调用 `WorkflowSurfaceBehavior.Refresh(host)`，让解析到的小地图再被推一次。

## 预期结果

- 小地图出现在画布右上角、滚动条上方。
- 每个可见或屏幕外的节点都有一块缩略图，以及一个当前视口的矩形。
- 滚动画布时，小地图里的视口矩形跟着移动。
- 不写 `MinimapOverlayName` 时覆盖层保持空白；不写 `ScrollViewerName` 时拖动小地图无法滚动表面。

## 下一页

[外观与导航](../02_外观与导航/index.md)介绍尺寸、样式、可见性与拖动。
