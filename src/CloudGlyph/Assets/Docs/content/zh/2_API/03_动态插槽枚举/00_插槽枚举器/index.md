# 插槽枚举器

`SlotEnumerator<TSlot>` 为每个选择器值持有一个 `ConditionalSlot<TSlot>`，并把选择器暴露为可绑定的 `CurrentValue`。安装会把自身注册到所属节点，因此只持有节点的调用方也能拿到端口。

命名空间：`VeloxDev.WorkflowSystem`。

**签名：** `partial class SlotEnumerator<TSlot> : IConditionalSlotProvider<TSlot>, IConditionalSlotProvider, INotifyPropertyChanged where TSlot : ISlotComponent, new()`

## 属性

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Parent` | `INodeComponent?` | 枚举器安装到的节点；未安装时为 null。 |
| `SelectorTypeName` | `string` | 选择器类型的存储名；序列化键。 |
| `SelectorType` | `Type?` | 解析后的选择器类型；protected setter。 |
| `Items` | `ObservableCollection<ConditionalSlot<TSlot>>` | 每个选择器值一项。 |
| `Count` | `int` | 冲刷延迟移除后的 `Items.Count`。 |
| `this[int index]` | `TSlot` | 索引处条目的插槽。 |
| `CurrentValue` | `object?` | 当前选中值。setter 会把值归一化到选择器类型并按选择器类型记录；getter 返回值的文本形式。 |

`CurrentValue` 从不记录 null：来自重建项源的瞬时 null 不会成为记忆中的选择。

## 方法

### SetSelector

**签名：** `void SetSelector(object? selector)`

由 `selector` 构建新端口集：

| selector 实参 | 端口 |
| --- | --- |
| 枚举 `Type` | 每个 `Enum.GetNames` 成员一个分支，按值顺序。 |
| `bool` 类型 | 两个分支：`false`、`true`。 |
| 全限定类型名字符串 | 用 `Type.GetType` 解析后按上述处理。 |
| `ISlotProvider` 实例 | 每个 `GetSlots()` 定义一个分支；`Value` 是路由键，`Label` 是显示名。 |

替换之前，它按两个方向捕获每个既有分支的连线。对于全新选择器类型，新分支会接到它所代表旧分支的邻居：

- 两个**枚举类型**之间，身份是**位置**；
- **同一提供者类型**之间，身份是**名称**，因此重排端口列表不会移动连线。

每个选择器类型的完整状态都会被记住，切回时恢复其分支、连线与选择。整个切换是树上的一个 `ActionPair`；未挂载节点直接应用状态，不产生撤销项。缺少父节点，或选择器无法解析为类型时，经 `WorkflowGuard.Fail`/`Debug.Fail` 失败，而不是抛异常。

用当前已安装的枚举类型调用会立即返回（`SelectorTypeName` 相等）。

### TrySelect

**签名：** `bool TrySelect(object value, out TSlot? slot)`

在条件表中查找 `value`。值没有分支时返回 `false` 且 `slot` 为 null。

### NormalizeSelectorValue

**签名：** `object? NormalizeSelectorValue(object? value)`

把 `value` 转换到当前选择器类型（枚举按名称不区分大小写解析，或 `Convert.ChangeType`）。无法转换时原样返回。`CurrentValue` 的写入按同样方式归一化，因此把读回值与枚举成员比较前先用本方法处理。

### Install / Uninstall

**签名：** `void Install(INodeComponent parent, string memberName)`、`void Uninstall()`

`Install` 设置 `Parent`、记住成员名用于变更通知，并在节点助手实现 `IConditionalSlotProviders` 时把枚举器加入其 `Providers`。`Uninstall` 移除它、清空条件表并分离所有插槽。

### OnDeserializing / OnDeserialized

**签名：** `void OnDeserializing(StreamingContext context)`、`void OnDeserialized(StreamingContext context)`

序列化钩子，公开是因为消费程序集要序列化自己闭合的 `SlotEnumerator<TSlot>`。前者在序列化器填充前清空 `Items` 与 `ConditionMap`；后者从 `SelectorTypeName` 重新解析 `SelectorType`、重新归一化每个分支值、重新校验 `CurrentValue`、重新填充每类型缓存，并把插槽重新挂到 `Parent`。

### GetEnumerator

**签名：** `IEnumerator<TSlot> GetEnumerator()`

遍历插槽（而非条目）。同时实现了非泛型 `IEnumerator IEnumerable.GetEnumerator()`。

## 显式接口成员

`IConditionalSlotProvider.Slots` 把 `Items` 作为 `IReadOnlyList<IConditionalSlot>` 返回；`IConditionalSlotProvider.TrySelect(object, out ISlotComponent?)` 转发到强类型方法。它们是不了解 `TSlot` 的调用方使用的擦除视图。

## 插槽向节点注册

分支被加入且枚举器有父节点时，插槽立即注册：

- 未挂载节点上，`parent.StandardCreateSlot(slot)` 作为普通集合加入执行；
- 已挂载节点上，`parent.CreateSlotCommand.Execute(slot)` 为每个插槽提交一个撤销项。

`StandardCreateSlot` 的幂等保护会让之后延迟派发的命令成为无操作，而不是产生幽灵撤销项。

## 示例

```csharp
var node = new NodeDefaultViewModel();
var ports = new SlotEnumerator<SlotDefaultViewModel>();
ports.Install(node, "OutputSlots");

ports.SetSelector(typeof(DayOfWeek));
Console.WriteLine($"{ports.Count} {ports.Items[0].Name} {ports.SelectorType?.Name}");

if (ports.TrySelect(DayOfWeek.Friday, out var friday))
    Console.WriteLine(friday!.State);   // StandBy

ports.CurrentValue = DayOfWeek.Friday;
Console.WriteLine(ports.CurrentValue);  // Friday
```
