# MVVM — 观察集合变化

当 `[VeloxProperty]` 成员的类型实现 `INotifyCollectionChanged`（`ObservableCollection<T>` 及大多数集合视图模型）时，生成器会自动把 `CollectionChanged` 接到你的钩子上 —— 既覆盖集合*内部*元素变化，也覆盖整个集合实例被*替换*的情况。

## 1. 声明集合属性

同样的特性，任何 `INotifyCollectionChanged` 类型：

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private ObservableCollection<string> _items = [];

    public CounterViewModel()
    {
        Items.Add("seed");
    }
}
```

**预期结果：** 生成 `public ObservableCollection<string> Items`。构造函数也可以使用属性的对象初始化器（`Items = [...]`）—— 为什么两种风格都被覆盖见第 3 节。

## 2. 生成的钩子

对于名为 `Items`、元素类型为 `string` 的属性，生成器发出：

```csharp
partial void OnItemsChanging(ObservableCollection<string> oldValue, ObservableCollection<string> newValue);
partial void OnItemsChanged(ObservableCollection<string> oldValue, ObservableCollection<string> newValue);

partial void OnItemAddedToItems(System.Collections.Generic.IEnumerable<string> items);
partial void OnItemRemovedFromItems(System.Collections.Generic.IEnumerable<string> items);
partial void OnItemMovedInItems(System.Collections.Generic.IEnumerable<string> items);
partial void OnItemsResetInItems();
```

`OnItemsChanging` / `OnItemsChanged` 这对钩子在整个集合实例被替换时触发（经由属性 setter，与标量的 `OnIndexChanged` 同理）。四个逐项钩子映射到底层事件的 `NotifyCollectionChangedAction`：

| `NotifyCollectionChangedAction` | 触发的钩子 |
|---|---|
| `Add` | `OnItemAddedToItems(newItems)` |
| `Remove` | `OnItemRemovedFromItems(oldItems)` |
| `Replace` | 先 `OnItemRemovedFromItems(oldItems)` 后 `OnItemAddedToItems(newItems)` |
| `Move` | `OnItemMovedInItems(newItems)` |
| `Reset` | `OnItemsResetInItems()` |

在你自己 partial 部分里实现任意一个即可。WPF 演示（`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`）为其 `Items` 集合实现了 `OnItemAddedToItems`、`OnItemRemovedFromItems`、`OnItemMovedInItems`、`OnItemsResetInItems`。

**预期结果：** `Items.Add("x")` 调用 `OnItemAddedToItems` 并携带新增项；`Items.Clear()` 调用 `OnItemsResetInItems`；替换整个集合实例调用 `OnItemsChanged`，随后通过 `OnItemAddedToItems` 对新增内容批量入钩。

## 3. 可重写的 `OnCollectionChanged<T>`

每个集合事件也会汇入单一重写点。当基类未提供时，生成器发出 `protected virtual void OnCollectionChanged<T>(string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)`；基类已声明的会被复用（演示在 `ObservableViewModelBase` 里重写了它）：

```csharp
public partial class CounterViewModel
{
    protected override void OnCollectionChanged<T>(
        string propertyName,
        System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
        System.Collections.Generic.IEnumerable<T>? oldItems,
        System.Collections.Generic.IEnumerable<T>? newItems)
    {
        System.Console.WriteLine($"{propertyName}: {e.Action}");
    }
}
```

**预期结果：** 每次 add/remove/move/replace/reset 除了逐项钩子之外，还会打印一行 `OnCollectionChanged<T>`。

## 4. 为什么订阅是懒加载的（`ObservableCollectionTracker`）

像 `_items = []` 这样的字段初始化器*直接*赋值后备字段，绕过生成的 setter —— 因此 setter 里的订阅步骤不会执行。`VeloxDev.MVVM.ObservableCollectionTracker` 补上这个缺口：生成的 getter 每次访问都调用 `ObservableCollectionTracker.EnsureSubscribed(value, OnItemsCollectionChanged)`，它通过 `ConditionalWeakTable` 保证恰好订阅一次（按“方法 + 目标”去重）。setter 在替换前对旧实例调用 `Unsubscribe`，因此处理器不会泄漏，被替换的集合也绝不会被再次订阅。

**预期结果：** 即使在字段初始化器里创建的集合，经过任意一次 getter 访问之后，钩子方法也会对新加入的元素触发；反复读 getter 不会增加重复订阅；tracker 永远不会让已被回收的集合存活。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。钩子名与动作映射来自 `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` 的 `MVVMPropertyFactory.GenerateCollectionMembers()`；tracker 语义来自 `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`；演示钩子来自 `Examples/MVVM/*/.../MainWindowViewModel.cs`。
