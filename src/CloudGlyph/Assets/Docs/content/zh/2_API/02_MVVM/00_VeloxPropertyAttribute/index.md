# MVVM — `VeloxPropertyAttribute`

`VeloxDev.MVVM.VeloxPropertyAttribute`（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`）标记一个成员，MVVM 源生成器会将其变成支持 `INotifyPropertyChanging` 和 `INotifyPropertyChanged` 的可通知属性。

**签名**

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **目标：** `Field` 或 `Property`。
- **标志：** `AllowMultiple = false`、`Inherited = false`。未密封。
- **备注：** 该特性本身不带任何参数；所有行为都由生成器（`VeloxDev.Generators.MVVM`，见 [MVVM](../08_MVVM/index.md)）根据被标记成员及其所在类决定。

## 字段形式（Demo 验证）

私有后备字段会被展开为公开属性。属性名通过去掉开头 `_` 并把下一个字母大写得到（`MVVMFieldAnalizer.GetPropertyNameFromFieldName`，`Base/Analizer.cs`）：`_index` → `Index`、`_selectedItem` → `SelectedItem`。

`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 25-29 行：

```csharp
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
```

由于属性是生成的，视图模型无需继承 MVVM 基类、也无需手动声明通知接口——类自身缺失的部分（事件、`OnPropertyChanging(string)` / `OnPropertyChanged(string)` 方法，或两个 `INotifyPropertyChanged` 接口）会由生成器补上。

## `partial` 属性形式（*推断所得*）

带 `[VeloxProperty]` 的 `partial` 属性由生成器补全（`MVVMWriter.ReadAutoProperties`）：它合成私有后备字段 `_{<首字母小写>}` 以及完整的 getter/setter。当前没有 Demo 使用该形式；此说明*由生成器源码推断*。

## 两种形式共享的生成行为

对每个被标记成员，生成器产出一个属性，其 setter：

1. 当 `Object.Equals(后备字段, value)` 成立时直接返回（无变化）；
2. 调用变更前通知 `OnPropertyChanging(string)`（基类或生成器提供）；
3. 调用按属性拆分的钩子 `partial void On{Name}Changing(T oldValue, T newValue)`；
4. 给后备字段赋值；
5. 调用 `partial void On{Name}Changed(T oldValue, T newValue)`；
6. 调用变更后通知 `OnPropertyChanged(string)`。

当成员类型实现 `INotifyCollectionChanged`（例如 `ObservableCollection<T>`）时，getter 还会通过 `ObservableCollectionTracker` 进行惰性订阅（见 [ObservableCollectionTracker](../07_ObservableCollectionTracker/index.md)），并生成按动作拆分的 `partial` 钩子（`OnItemAddedTo{Name}`、`OnItemRemovedFrom{Name}`、`OnItemMovedIn{Name}`、`OnItemsResetIn{Name}`），以及一个转发到 `OnCollectionChanged<T>` 的私有 `On{Name}CollectionChanged` 处理器。

`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 34-37 行 — 响应 `Index` 变化的按属性钩子：

```csharp
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // notify that MinusCommand's executability needs to be refreshed
}
```

其中的 `MinusCommand` 是 Command 生成器从带 `[VeloxCommand]` 的 `Minus` 方法派生的命令属性（见 [VeloxCommandAttribute](../01_VeloxCommandAttribute/index.md)）。
