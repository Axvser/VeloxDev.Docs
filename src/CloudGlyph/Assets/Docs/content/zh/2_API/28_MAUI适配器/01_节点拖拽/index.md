# 节点拖拽

`WorkflowNodeDragBehavior` 把节点卡片上的拖动变成 `MoveCommand`。Windows 上适配器捕获指针；其他平台在 MAUI 平移手势开始后交由它接管拖拽，因为原生指针捕获在某些平台不可用。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.MAUI`。

## WorkflowNodeDragBehavior

**签名：** `sealed class WorkflowNodeDragBehavior`（静态附着属性类，不继承 `BindableObject`）

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 把元素上的拖动变成节点移动。 |
| `CoordinateHostName` | `string?` | `null` | 增量所依据的坐标空间元素。 |
| `CoordinateHostType` | `Type?` | `null` | 用于解析坐标宿主的类型。 |

访问器：`GetIsEnabled` / `SetIsEnabled`、`GetCoordinateHostName` / `SetCoordinateHostName`、`GetCoordinateHostType` / `SetCoordinateHostType`，均接收 `BindableObject`。

```xml
<Grid Grid.Row="0" BackgroundColor="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <Label Text="{Binding Name}" Margin="10,0" VerticalTextAlignment="Center" />
</Grid>
```

**预期结果：** 拖动卡片会移动绑定节点；默认不会加入撤销历史。
