# 画布变换与节点拖拽

WPF 那一对行为的 Avalonia 对应版本。变换行为携带一个 `ITransform?` 附着值，节点与连线模板把 `RenderTransform` 绑到它；拖拽行为以指针增量执行 `MoveCommand`。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.Avalonia`。

## WorkflowCanvasTransformBehavior

**签名：** `sealed class WorkflowCanvasTransformBehavior : AvaloniaObject`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `TransformProperty` | `AttachedProperty<ITransform?>` | 附着变换。 |
| `GetTransform(AvaloniaObject element)` | `static ITransform?` | 读取变换。 |
| `SetTransform(AvaloniaObject element, ITransform? value)` | `static void` | 写入变换。 |

该属性只是通知载体：宿主控件刻意不接收渲染变换；节点与连线视图各自绑定自己的变换。使用编译绑定时写作：

```xml
RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
```

## WorkflowNodeDragBehavior

**签名：** `sealed class WorkflowNodeDragBehavior : AvaloniaObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 把元素上的拖动变成节点移动。 |
| `CoordinateHostName` | `string?` | `null` | 增量所依据的坐标空间元素。 |
| `CoordinateHostType` | `Type?` | `null` | 用于解析坐标宿主的类型。 |

访问器：`GetIsEnabled` / `SetIsEnabled`、`GetCoordinateHostName` / `SetCoordinateHostName`、`GetCoordinateHostType` / `SetCoordinateHostType`，均接收 `AvaloniaObject`。

```xml
<Grid Height="32" VerticalAlignment="Top" Background="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <TextBlock Text="{Binding Name}" Margin="10,8" />
</Grid>
```

**预期结果：** 拖动该元素会移动绑定节点；执行的是节点的 `MoveCommand`，默认不会进入撤销历史。
