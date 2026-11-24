# 画布变换与节点拖拽

变换行为携带一个 `Transform?` 附着值，供绑定 `RenderTransform` 的视图使用；WinUI 上表面本身不用它做平移。拖拽行为把拖动变成 `MoveCommand`。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WinUI`。

## WorkflowCanvasTransformBehavior

**签名：** `static class WorkflowCanvasTransformBehavior`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `TransformProperty` | `DependencyProperty` | 附着变换。 |
| `GetTransform(UIElement element)` | `static Transform?` | 读取变换。 |
| `SetTransform(UIElement element, Transform? value)` | `static void` | 写入变换。 |

表面通过组合平移移动画布；此属性服务于偏好渲染变换的视图。

## WorkflowNodeDragBehavior

**签名：** `sealed class WorkflowNodeDragBehavior : DependencyObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 把元素上的拖动变成节点移动。 |
| `CoordinateHostName` | `string?` | `null` | 增量所依据的坐标空间元素。 |
| `CoordinateHostType` | `Type?` | `null` | 用于解析坐标宿主的类型。 |

访问器：`GetIsEnabled` / `SetIsEnabled`、`GetCoordinateHostName` / `SetCoordinateHostName`、`GetCoordinateHostType` / `SetCoordinateHostType`。

该行为在启动手势前先路由按下，因为 WinUI 没有隧道/预览指针阶段。订阅者在按下时设置 `PreventDefault` 可阻止拖拽开始。

```xml
<Grid Height="32" VerticalAlignment="Top" Background="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <TextBlock Text="{Binding Name}" Margin="10,8" />
</Grid>
```

**预期结果：** 拖动该元素会移动绑定节点；按下先经 `WorkflowInput` 路由，宿主因此可以拒绝该手势。
