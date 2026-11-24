# 插槽行为

连接行为开始并完成连接拖拽，且在 MAUI 上还要报告候选接收端，因为共享连线覆盖层无法对插槽做命中测试。布局行为测量端口并写入锚点。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.MAUI`。

## WorkflowSlotConnectionBehavior

**签名：** `sealed class WorkflowSlotConnectionBehavior`（静态附着属性类）

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `IsEnabledProperty` | `BindableProperty` | 附着开关，默认 `false`。 |
| `GetIsEnabled(BindableObject)` / `SetIsEnabled(BindableObject, bool)` | 访问器 | 读取或写入开关。 |
| `SetIsDraggingConnection(bool isDraggingConnection)` | `static void` | 告知行为是否正在拖拽连接，以便它报告候选接收端。 |

Windows 上适配器捕获指针；其他平台在 MAUI 平移手势开始后交由它接管。两个标准命令不变，行为不裁决合法性。

```xml
<Ellipse x:Name="PART_InputSlot" Grid.Row="1" BindingContext="{Binding InputSlot}"
         WidthRequest="14" HeightRequest="14" Fill="#FF1E1E1E" Stroke="White"
         HorizontalOptions="Start" VerticalOptions="Center"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

**预期结果：** 在一个端口按下、在另一端口松开即连接；在空白画布松开则取消。

## WorkflowSlotLayoutBehavior

**签名：** `sealed class WorkflowSlotLayoutBehavior`（静态附着属性类）

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
| `Refresh` | `static void Refresh(ContentView control)` | 针对当前视口重新测量所有命名端口。 |

```xml
<Border behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
        behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
        behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
        behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
```

**预期结果：** 布局之后，每个端口的 `ISlotComponent.Anchor` 与其视觉中心一致；用这些锚点绘制的连线正好接上端口。
