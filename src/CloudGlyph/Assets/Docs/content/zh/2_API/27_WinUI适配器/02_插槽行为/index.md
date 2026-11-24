# 插槽行为

连接行为借助指针捕获的松开模拟缺失的隧道阶段；插槽布局行为以**画布局部**测量端口，并通过 `SlotAnchorFromCanvasLocal` 写入锚点。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WinUI`。

## WorkflowSlotConnectionBehavior

**签名：** `sealed class WorkflowSlotConnectionBehavior : DependencyObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 启用“按下发送 / 松开接收”。 |

访问器：`GetIsEnabled` / `SetIsEnabled`。

两个标准命令不变。该行为不裁决合法性；那是 `ITreeHelper.ValidateConnection` 与 `ITreeEvents.Connecting` 否决的职责。

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

**预期结果：** 在一个端口按下、在另一个端口松开即创建连线；在空白画布松开则取消。

## WorkflowSlotLayoutBehavior

**签名：** `sealed class WorkflowSlotLayoutBehavior : DependencyObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 测量命名端口并写入锚点。 |
| `SlotNames` | `string?` | `null` | 命名单端口。 |
| `SlotEnumeratorNames` | `string?` | `null` | 命名枚举器，其条目暴露端口。 |
| `CoordinateHostName` | `string?` | `null` | 锚点使用的坐标空间元素。 |
| `CoordinateHostType` | `Type?` | `null` | 用于解析坐标宿主的类型。 |

访问器：`GetIsEnabled` / `SetIsEnabled`、`GetSlotNames` / `SetSlotNames`、`GetSlotEnumeratorNames` / `SetSlotEnumeratorNames`、`GetCoordinateHostName` / `SetCoordinateHostName`、`GetCoordinateHostType` / `SetCoordinateHostType`。WinUI 的该行为没有公开 `Refresh`；表面在自己的布局刷新中重新测量它。

此适配器上的锚点以**画布局部**测量，并通过 `SlotAnchorFromCanvasLocal` 写入。使用视觉中心形式会再减一次 `ActualOffset`，使每条连线整体偏移一个常量。

```xml
<Grid behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
      behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
      behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
      behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
```

**预期结果：** 连线在 100% 与 40% 缩放下都接上端口，平移画布时不会整体偏移。
