# 连线覆盖层

`WorkflowLinkOverlay` 是单个 `GraphicsView`，在一个视口尺寸的层里绘制可见集合中的全部连线以及虚拟预览。它必须位于不断增长的世界画布之外：画布尺寸的 `GraphicsView` 在深缩放下会超过 Win2D 约 16k 设备像素的纹理上限，整层会无声消失。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.MAUI`。

## WorkflowLinkOverlay

**签名：** `sealed class WorkflowLinkOverlay : GraphicsView`

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `WorkflowTree` | `ITreeComponent?` | `null` | 要绘制其连线的树。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | 表面滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | 画布内容偏移。 |
| `RulerThickness` | `double` | `0` | 要避让的标尺带。 |
| `LinkLineColor` | `Color?` | 半透明白 | 静止连线颜色。 |
| `VirtualLineColor` | `Color?` | 半透明白 | 没有阶段颜色时的虚拟连线颜色。 |
| `VirtualValidTargetColor` | `Color?` | `null` | 悬停在合法接收端上的虚拟连线颜色；`null` 保持 `VirtualLineColor`。 |
| `VirtualInvalidTargetColor` | `Color?` | `null` | 悬停在拒绝连接的插槽上的虚拟连线颜色；`null` 保持 `VirtualLineColor`。 |
| `StrokeWidth` | `double` | `4` | 连线线宽。 |
| `LinkFlowEnabled` | `bool` | `false` | 启用流动高亮。 |
| `InteractionSource` | `View?` | `null` | 其指针/键盘输入驱动连线交互的视图。 |
| `BandCentre` | `double` | 运行时 | 流动带在连线长度上的位置比例。 |
| `BandMix` | `double` | 运行时 | 流动带混合系数。 |

覆盖层 `InputTransparent = true`；`InteractionSource` 才是让连线可悬停、可删除的机制。把它设为已位于表面输入路径上的视图（画布的祖先），绝不要设为覆盖层自身。不设它，连线会绘制但永不响应指针。

覆盖层只绘制**静止**连线。悬停高亮属于宿主：订阅树的 `IInputEvents`，读取连线发布的曲线，并在上方绘制自己的层。

```xml
<behaviors:WorkflowLinkOverlay x:Name="PART_LinkLayer"
                               WorkflowTree="{Binding BindingContext, Source={x:Reference Root}}"
                               InteractionSource="{x:Reference Root}"
                               ScrollOffsetX="{Binding ScrollOffsetX, Source={x:Reference PART_GridDecorator}}"
                               ScrollOffsetY="{Binding ScrollOffsetY, Source={x:Reference PART_GridDecorator}}"
                               ContentOffsetX="{Binding ContentOffsetX, Source={x:Reference PART_GridDecorator}}"
                               ContentOffsetY="{Binding ContentOffsetY, Source={x:Reference PART_GridDecorator}}"
                               RulerThickness="0" StrokeWidth="2" />
```

**预期结果：** 两个插槽锚点测量完成后连线出现；悬停绘制主体（两侧六单位）可命中连线，Delete 通过其 `DeleteCommand` 删除悬停连线。
