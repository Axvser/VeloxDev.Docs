# 条件插槽与提供者

条目把一个选择器值与为它构建的插槽配对。端口不是枚举成员时由提供者给出条目，节点助手则通过一个擦除接口暴露所有已安装的枚举器。

命名空间：`VeloxDev.WorkflowSystem`；`SlotSelectorsAttribute` 例外，位于 `VeloxDev.AI`。

## IConditionalSlot

**签名：** `interface IConditionalSlot`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Name` | `string` | 条目的显示标签。 |
| `Value` | `object?` | 条目对应的选择器值。 |
| `Slot` | `ISlotComponent` | 为条目构建的插槽。 |

## ConditionalSlot<T>

**签名：** `partial class ConditionalSlot<TSlot> : IConditionalSlot where TSlot : ISlotComponent, new()`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Name` | `string` | 标签；默认空。 |
| `Value` | `object?` | 选择器值。 |
| `Slot` | `TSlot` | 插槽；由 `TSlot` 的默认构造函数创建。 |
| `IConditionalSlot.Slot` | `ISlotComponent` | 强类型属性上的显式实现。 |

## SlotDefinition

**签名：** `sealed class SlotDefinition(object value, string label = "")`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `SlotDefinition(object value, string label = "")` | 构造函数 | 保存路由键与标签。 |
| `Value` | `object` | `TrySelect` 使用的路由键。 |
| `Label` | `string` | 显示名；为空时回退到 `Value`。 |

## ISlotProvider

**签名：** `interface ISlotProvider`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `GetSlots()` | `IEnumerable<SlotDefinition>` | 有序定义；每个成为一条 `ConditionalSlot<TSlot>`。 |

提供者是**值**而不是类型：把同类型的另一个实例传给 `SetSelector` 会从该实例重建端口，而不是恢复快照。这正是智能体能反复重塑节点端口的原因。要跨序列化往返，请给提供者加 `[Archivable]` 并让其模型可序列化。

## IConditionalSlotProvider<T>

**签名：** `interface IConditionalSlotProvider<TSlot> : IEnumerable<TSlot> where TSlot : ISlotComponent, new()`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Parent` | `INodeComponent?` | 已安装节点，或 null。 |
| `SelectorTypeName` | `string` | 存储的选择器类型名。 |
| `Items` | `ObservableCollection<ConditionalSlot<TSlot>>` | 分支。 |
| `CurrentValue` | `object?` | 选中值。 |
| `TrySelect(object value, out TSlot? slot)` | `bool` | 路由查找。 |
| `SetSelector(object? selector)` | `void` | 切换选择器。 |
| `Install(INodeComponent parent, string memberName)` | `void` | 绑定到节点。 |
| `Uninstall()` | `void` | 分离。 |

## IConditionalSlotProvider

**签名：** `interface IConditionalSlotProvider` —— 类型擦除视图。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Parent` | `INodeComponent?` | 已安装节点。 |
| `SelectorTypeName` | `string` | 存储的类型名。 |
| `SelectorType` | `Type?` | 已解析的选择器类型。 |
| `CurrentValue` | `object?` | 选中值。 |
| `Slots` | `IReadOnlyList<IConditionalSlot>` | 当前分支。 |
| `TrySelect(object value, out ISlotComponent? slot)` | `bool` | 路由查找。 |
| `SetSelector(object? selector)` | `void` | 切换选择器。 |

## IConditionalSlotProviders

**签名：** `interface IConditionalSlotProviders`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Providers` | `IList<IConditionalSlotProvider>` | 节点的枚举器，按安装顺序。 |

`NodeHelper<T>` 实现该接口。`SlotEnumerator<TSlot>.Install` 加入 `Providers`，`Uninstall` 移除，因此读取方应把它当作只读列表。

## SlotSelectorsAttribute

**签名：** `sealed class SlotSelectorsAttribute : Attribute`，`AttributeTargets.Property | AttributeTargets.Field`。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `SlotSelectorsAttribute(params Type[] allowedEnumTypes)` | 构造函数 | 编译期安全列表；同时推导 `AllowedEnumTypeNames`。 |
| `SlotSelectorsAttribute(params string[] allowedEnumTypeNames)` | 构造函数 | 便于序列化的名称；`AllowedEnumTypes` 保持为空。 |
| `AllowedEnumTypes` | `Type[]` | 允许的选择器类型。 |
| `AllowedEnumTypeNames` | `string[]` | 全限定名，便于序列化。 |

该特性声明**智能体工具**（`ListSlotProperties`、`SetEnumSlotCollection`）可对该成员使用哪些选择器类型。它不驱动枚举器：直接代码可用任意枚举、`bool` 或提供者调用 `SetSelector`。被标注的属性会被 `PatchNodeProperties` 拒绝；枚举插槽工具是受认可的修改路径。

两个成员都为空表示接受任意类型。

## 示例

```csharp
public sealed class PortProvider(params string[] names) : ISlotProvider
{
    public IEnumerable<SlotDefinition> GetSlots()
        => names.Select(name => new SlotDefinition(name, name));
}

var node = new NodeDefaultViewModel();
var ports = new SlotEnumerator<SlotDefaultViewModel>();
ports.Install(node, "OutputSlots");
ports.SetSelector(new PortProvider("stats", "dist", "anomalies"));

Console.WriteLine(string.Join(",", ports.Items.Select(i => i.Name))); // stats,dist,anomalies
Console.WriteLine(ports.TrySelect("dist", out var dist));            // True

// 从同类型另一实例重建：分支按名称配对。
ports.SetSelector(new PortProvider("stats", "trend"));
Console.WriteLine(ports.Count);                                      // 2
```
