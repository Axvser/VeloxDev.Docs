# 插槽行为

连接行为开始并完成连接拖拽；插槽布局行为测量端口并写入 `Anchor`。Avalonia 适配器在按下时释放指针捕获，好让松开事件到达接收端口。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.Avalonia`。

## WorkflowSlotConnectionBehavior

**签名：** `sealed class WorkflowSlotConnectionBehavior : AvaloniaObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 启用“按下发送 / 松开接收”。 |

访问器：`GetIsEnabled` / `SetIsEnabled`，接收 `AvaloniaObject`。

该行为执行两个标准命令，不裁决连接是否合法；那是 `ITreeHelper.ValidateConnection` 与 `ITreeEvents.Connecting` 否决的职责。

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

**预期结果：** 在一个端口按下、在另一个端口松开即创建连线；在空白画布松开则清除预览。

## WorkflowSlotLayoutBehavior

**签名：** `sealed class WorkflowSlotLayoutBehavior : AvaloniaObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 测量命名端口并写入锚点。 |
| `SlotNames` | `string?` | `null` | 命名单端口。 |
| `SlotEnumeratorNames` | `string?` | `null` | 命名枚举器，其条目暴露端口。 |
| `CoordinateHostName` | `string?` | `null` | 锚点使用的坐标空间元素。 |
| `CoordinateHostType` | `Type?` | `null` | 用于解析坐标宿主的类型。 |

访问器：`GetIsEnabled` / `SetIsEnabled`、`GetSlotNames` / `SetSlotNames`、`GetSlotEnumeratorNames` / `SetSlotEnumeratorNames`、`GetCoordinateHostName` / `SetCoordinateHostName`、`GetCoordinateHostType` / `SetCoordinateHostType`。

| 方法 | 签名 | 说明 |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl control)` | 重新测量所有命名端口。 |

该行为通过 `SlotLayoutPipelineCore` 在滚动空间测量每个端口，跳过 `Bounds` 尚未测量的端口。

```xml
<Grid behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
      behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
      behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
      behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
```

**预期结果：** 布局之后，每个端口的 `ISlotComponent.Anchor` 与其在画布空间中的视觉中心一致，用这些锚点绘制的连线正好接上端口。
