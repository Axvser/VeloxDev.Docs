# MVVM — `VeloxPropertyAttribute`

`VeloxDev.MVVM.VeloxPropertyAttribute`（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`）标记一个成员，由 MVVM 源生成器转换为变更通知属性。

## Class: `VeloxPropertyAttribute`

**Signature**

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **基类型：** `System.Attribute`。**非 sealed。**
- **目标：** `Field` 或 `Property`。`AllowMultiple = false`、`Inherited = false`。
- **构造函数：** 只有隐式无参构造函数。
- **成员：** 无 —— 纯标记类型。

**说明：** 所有行为由 `VeloxDev.Generators.MVVM` 根据被标注成员及其所在类决定。所在类型必须是 `partial`；被标注字段必须是字段，被标注属性必须是 C# 13 `partial` 属性。

## 生成的成员

对于 `[VeloxProperty] private int _count;`：

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if(global::System.Object.Equals(this._count, value)) return;
        var old = this._count;
        OnPropertyChanging(nameof(Count));
        OnCountChanging(old, value);
        this._count = value;
        OnCountChanged(old, value);
        OnPropertyChanged(nameof(Count));
    }
}
partial void OnCountChanging(System.Int32 oldValue, System.Int32 newValue);
partial void OnCountChanged(System.Int32 oldValue, System.Int32 newValue);
```

命名：去掉开头的 `_` 并把下一个字符大写（`_index` → `Index`、`_selectedItem` → `SelectedItem`）。推不出合法标识符的名字报告 `VELOX_MVVM_PROP002`。

##### Property: `{Name}`

类型与标注成员相同的公开属性。setter 先做 `Object.Equals` 短路（浮点类型改比位模式，以保留 `-0.0` 与 `NaN`），触发 `OnPropertyChanging(nameof({Name}))`，调用 `partial On{Name}Changing(old, new)`，赋值，调用 `partial On{Name}Changed(old, new)`，最后触发 `OnPropertyChanged(nameof({Name}))`。

对于 `partial` 属性形态，生成器保留你声明的可访问性与访问器可见性，并生成名为 `_{camelCaseName}` 的 backing field，除非已存在同名的可访问字段。

##### Hook: `On{Name}Changing(T oldValue, T newValue)`

`partial void`。由生成器声明，由你实现（或留空）。在赋值前运行。

##### Hook: `On{Name}Changed(T oldValue, T newValue)`

`partial void`。在赋值后运行。

##### 集合成员（`INotifyCollectionChanged` 类型）

getter 通过 `ObservableCollectionTracker.EnsureSubscribed` 惰性订阅；setter 先解绑旧实例、对旧项调用 `OnItemRemovedFrom{Name}`，赋值后再对新项调用 `OnItemAddedTo{Name}`。

| 成员 | 签名 |
| --- | --- |
| `OnItemAddedTo{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemRemovedFrom{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemMovedIn{Name}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemsResetIn{Name}` | `partial void ()` |
| `OnCollectionChanged<T>` | `protected virtual void (string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)` |

无法确定集合项类型时，钩子接收非泛型 `IEnumerable`。

## 诊断

| Id | 级别 | 条件 |
| --- | --- | --- |
| `VELOX_MVVM_PROP001` | Error | 两个成员映射到同一个属性名，或已有字段无法支撑该属性 |
| `VELOX_MVVM_PROP002` | Warning | 字段名推不出合法标识符 |
| `VELOX_MVVM_PROP003` | Warning | 被标注的属性不是 `partial` |

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
[VeloxProperty] private string _collectionStatus = "等待集合通知";
[VeloxProperty] private string _collectionTrace = "OnCollectionChanged<T> 尚未触发";
```

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify();
}

partial void OnSelectedItemChanged(string? oldValue, string? newValue)
{
    SelectedItemSummary = newValue is null ? "当前选中: (无)" : $"当前选中: {newValue}";
    RemoveSelectedItemCommand.Notify();
}
```

**说明：**

- 该特性不继承、不可重复应用。
- 不需要 MVVM 基类。生成器补齐类中缺少的部分：事件、`OnPropertyChanging(string)` / `OnPropertyChanged(string)`，或两个接口。它也会识别 CommunityToolkit.Mvvm、Prism、ReactiveUI 与 Caliburn.Micro 基类并委托给它们的通知器。
- 示例使用字段形态；`partial` 属性形态由同一写入器（`ReadAutoProperties`）实现，由 `McpServerConfiguration.cs` 使用，MVVM 示例未覆盖它。
