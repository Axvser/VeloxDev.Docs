# 画布变换与节点拖拽

两个小型附着行为。变换行为是一个值载体，节点与连线模板把 `RenderTransform` 绑定到它；拖拽行为把节点上的拖动变成 `MoveCommand`。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WPF`。

## WorkflowCanvasTransformBehavior

**签名：** `static class WorkflowCanvasTransformBehavior`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `TransformProperty` | `DependencyProperty` | 携带画布变换的附着属性。 |
| `GetTransform(UIElement element)` | `static Transform?` | 读取变换。 |
| `SetTransform(UIElement element, Transform? value)` | `static void` | 写入变换。 |

表面写入当前变换，模板绑定到它。绑定必须位于 `DataTemplate` 根上，因为从嵌套视图内部做祖先查找会解析到条目自己的树：

```xml
RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                          Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
```

## WorkflowNodeDragBehavior

**签名：** `sealed class WorkflowNodeDragBehavior : DependencyObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 把元素上的拖动变成节点移动。 |
| `CoordinateHostName` | `string?` | `null` | 拖拽增量所依据的坐标空间元素。 |
| `CoordinateHostType` | `Type?` | `null` | 没有提供名称时用于解析坐标宿主的类型。 |

访问器：`GetIsEnabled` / `SetIsEnabled`、`GetCoordinateHostName` / `SetCoordinateHostName`、`GetCoordinateHostType` / `SetCoordinateHostType`。

该行为以拖拽增量执行节点的 `MoveCommand`。默认情况下 `Move` / `SetAnchor` / `SetSize` 不会进入撤销历史，因此除非宿主提交该变化，普通拖拽不可撤销。

```xml
<Grid Grid.Row="0" Background="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <TextBlock Text="{Binding Name}" VerticalAlignment="Center" Margin="10,0" />
</Grid>
```

**预期结果：** 拖动该元素会按 `PART_Canvas` 空间中的指针增量移动绑定节点。
