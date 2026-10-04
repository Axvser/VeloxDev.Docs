# MVVM — `VeloxPropertyAttribute`

`VeloxDev.MVVM.VeloxPropertyAttribute`（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`）标记一个成员，MVVM 源生成器会把它变成支持 `INotifyPropertyChanging` 与 `INotifyPropertyChanged` 的可通知属性。

## Class: `VeloxPropertyAttribute`

**Signature**

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **基类型：** `System.Attribute`。**不是** `sealed`。
- **目标：** `Field` 或 `Property`。
- **标志：** `AllowMultiple = false`、`Inherited = false`。
- **构造函数：** 只有隐式的无参构造函数。
- **属性 / 方法：** 未声明任何成员 —— 这是一个纯标记特性。

**Notes:**

- 特性没有参数；所有行为都由生成器（`VeloxDev.Generators.MVVM`，见 `13_MVVM` 页）根据被标注成员及其所在类决定。
- 所在类必须是 `partial`，被标注的成员必须是字段（不能是局部变量或捕获变量）。

## 生成的成员

生成器把属性及其钩子写进同一个类的另一个 partial 部分。对于 `[VeloxProperty] private int _count;`，生成的属性逐字为：

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if (global::System.Object.Equals(this._count, value)) return;
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

命名规则：去掉前导 `_` 并把下一个字符大写（`_index` → `Index`，`_selectedItem` → `SelectedItem`）。

## 按成员种类生成的成员

##### 属性：`{名称}`

类型与被标注成员相同的公开属性。setter 先在 `Object.Equals` 处短路，然后依次触发 `OnPropertyChanging(nameof({名称}))`、调用 `partial On{名称}Changing(old, new)`、赋值、调用 `partial On{名称}Changed(old, new)`、触发 `OnPropertyChanged(nameof({名称}))`。

##### 钩子：`On{名称}Changing(T oldValue, T newValue)`

`partial void`。由生成器声明，由你实现（或留空）。在赋值**之前**运行。

##### 钩子：`On{名称}Changed(T oldValue, T newValue)`

`partial void`。在赋值**之后**运行。

##### 集合成员（`INotifyCollectionChanged` 类型）

getter 经 `ObservableCollectionTracker.EnsureSubscribed` 懒加载订阅，setter 对旧实例退订。在 changing/changed 这一对之外，还会增加四个按动作钩子与一个重写点：

| 成员 | 签名 |
|---|---|
| `On{名称}Changing` / `On{名称}Changed` | `partial void (TCollection oldValue, TCollection newValue)` |
| `OnItemAddedTo{名称}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemRemovedFrom{名称}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemMovedIn{名称}` | `partial void (IEnumerable<TItem> items)` |
| `OnItemsResetIn{名称}` | `partial void ()` |
| `OnCollectionChanged<T>` | `protected virtual void (string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)` |

## Example

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 25-31
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
[VeloxProperty] private string _collectionStatus = "等待集合通知";
```

```csharp
// Source: Demo — Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 34-43
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // notify that MinusCommand's executability needs to be refreshed
}

partial void OnSelectedItemChanged(string? oldValue, string? newValue)
{
    SelectedItemSummary = newValue is null ? "当前选中: (无)" : $"当前选中: {newValue}";
    RemoveSelectedItemCommand.Notify();
}
```

**Notes:**

- 该特性不继承、不可重复：每个成员标注一次。
- 由于属性是生成的，视图模型不需要 MVVM 基类 —— 生成器会补齐类尚未提供的部分（事件、`OnPropertyChanging(string)` / `OnPropertyChanged(string)`，或两个接口）。它还能识别 CommunityToolkit.Mvvm、Prism、ReactiveUI 与 Caliburn.Micro 基类，并改为委托给它们的通知方法。
- `partial` 属性写法（`[VeloxProperty] public partial string Greeting { get; set; }`）在本模块的页面中属于*由生成器源码推断*；WPF/Avalonia 演示使用的字段写法是 Demo 实证的。
