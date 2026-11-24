# 外观与导航

覆盖层暴露普通依赖属性；宿主可以从 XAML 设置样式，也可以派生子类改绘制。导航不需要写代码：管线把一次按下与拖动通过适配器的视口层变成滚动偏移。

## 尺寸与放置

| 属性 | 默认 | 含义 |
|---|---:|---|
| `MinimapWidth` / `MinimapHeight` | 200 / 140 | 请求尺寸，之后被可用角落夹取。 |
| `MinimapMinSize` | 20 | 小地图可缩到的最小宽或高。 |
| `MinimapMargin` | 12 | 离可用角落的间隙。 |
| `ContentPadding` | 2 | 映射内容周围的内边距。 |
| `MinimapCornerRadius` | 4 | 外框圆角。 |
| `NodeCornerRadius` | 1 | 缩略块圆角。 |
| `IsMinimapVisible` | `true` | 为 `false` 时，渲染趟什么也不画。 |

位置不是属性：管线用表面推来的 `AvailableRight` / `AvailableTop` / `AvailableBottom` 计算矩形。因此在覆盖层上设置 `MinimapMargin` 也会改变表面为它让出的间隙。

## 画刷

| 属性 | 默认用途 |
|---|---|
| `MinimapBackground` | 地图背后的半透明面板。 |
| `MinimapBorderBrush`、`MinimapBorderThickness` | 外框描边。 |
| `NodeBrush` | 节点缩略块。 |
| `ViewportFill`、`ViewportStroke`、`ViewportStrokeThickness` | 视口指示块及其描边。 |

覆盖层声明了 `LinkBrush` 与 `LinkStrokeThickness`，但默认的 `DrawMinimap` 不画连线：`MinimapDrawContext` 只携带节点与视口矩形。想画连线的子类要从 `context.Tree` 自己算并绘制。

## 切换可见性

```xml
<CheckBox Content="Show minimap"
          IsChecked="{Binding IsMinimapVisible, ElementName=PART_MinimapOverlay}" />
```

`IsMinimapVisible` 是普通依赖属性，元素绑定或视图模型属性都可以。

## 拖动导航

在小地图矩形内按下时：

1. 刷新缓存映射，
2. 通过 `WorkflowSurfaceMath.MinimapToCanvasLocal` 把按下点从小地图局部坐标换算到画布局部坐标，
3. 通过 `WorkflowSurfaceMath.MinimapToScroll` 换算成滚动偏移，
4. 通过适配器的 `IMinimapViewportHost` 写入偏移。

按住期间每次移动重复第 2–4 步，视口跟随指针。松开结束拖动。按下命中测试针对放置后的小地图矩形，而不是视口指示块，所以点击地图里任何一点都会跳过去。

拖动数学在 Core；适配器只提供三个方法——读当前滚动偏移、读视口尺寸、应用偏移。

## 自定义绘制

```csharp
public sealed class BrandMinimap : WorkflowMinimapOverlay
{
    public BrandMinimap()
    {
        MinimapBackground = new SolidColorBrush(Color.FromArgb(0xD2, 0x1F, 0x1F, 0x1F));
        NodeBrush = new SolidColorBrush(Color.FromArgb(0xDC, 0x6E, 0x8B, 0xFF));
        ViewportStroke = Brushes.White;
    }

    protected override void DrawMinimap(DrawingContext dc, MinimapDrawContext context)
    {
        base.DrawMinimap(dc, context);
        // context.MappedNodes / context.MappedViewport are minimap-local and already padded.
    }
}
```

重写并调用 `base` 是在默认绘制上追加；完全替换则自己画。`MinimapDrawContext` 每个渲染趟至多重算一次；不要跨趟缓存它。

## 预期结果

- 改 `MinimapWidth` 会改变地图尺寸与映射比例。
- 切换 `IsMinimapVisible` 会在下一次渲染隐藏地图；表面照常运行。
- 在地图里拖动会连续平移画布；视口矩形跟着指针走。
- 只设置画刷的子类只改颜色，不碰映射。

## 下一页

[验证](../03_验证/index.md)把覆盖层放进宿主，并给出完整代码。
