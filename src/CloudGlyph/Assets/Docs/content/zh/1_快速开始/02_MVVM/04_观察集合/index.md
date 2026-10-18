# MVVM — 观察集合变化

当 `[VeloxProperty]` 成员的类型实现 `INotifyCollectionChanged`（例如 `ObservableCollection<T>`）时，生成器会自动订阅：既包括集合内部项的变化，也包括整个集合实例被替换。

## 1. 声明集合属性

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private ObservableCollection<string> _items = [];

    public CounterViewModel()
    {
        Items.Add("ready");
    }
}
```

**预期结果：** 生成 `public ObservableCollection<string> Items`；即使字段初始化器绕过了 setter，`Items.Add("ready")` 也会被观察。

## 2. 生成的钩子面

对于名为 `Items`、项类型为 `string` 的属性：

```csharp
partial void OnItemsChanging(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);
partial void OnItemsChanged(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);

partial void OnItemAddedToItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemRemovedFromItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemMovedInItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemsResetInItems();
```

前一对在整个实例通过 setter 被替换时触发。四个按项钩子由生成的 `OnItemsCollectionChanged` 处理器分发：

| `NotifyCollectionChangedAction` | 触发的钩子 |
| --- | --- |
| `Add` | `OnItemAddedToItems(e.NewItems)` |
| `Remove` | `OnItemRemovedFromItems(e.OldItems)` |
| `Replace` | 先 `OnItemRemovedFromItems(e.OldItems)`，再 `OnItemAddedToItems(e.NewItems)` |
| `Move` | `OnItemMovedInItems(e.NewItems)` |
| `Reset` | `OnItemsResetInItems()` |

**预期结果：** `Items.Add("x")` 会到达 `OnItemAddedToItems`；`Items.Clear()` 会到达 `OnItemsResetInItems`；替换整个实例会调用 `OnItemsChanging` / `OnItemsChanged`，并把旧项报告为移除、新项报告为添加。

## 3. `OnCollectionChanged<T>` 重写点

每个集合事件都会先汇入这一个重写点。当没有基类提供它时，生成器发出：

```csharp
protected virtual void OnCollectionChanged<T>(
    string propertyName,
    global::System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
    global::System.Collections.Generic.IEnumerable<T>? oldItems,
    global::System.Collections.Generic.IEnumerable<T>? newItems)
{
}
```

已有基类声明它时会复用之。示例的 `ObservableViewModelBase` 将其声明为 `protected virtual`，`MainWindowViewModel` 重写它来写入一行追踪文本。

**预期结果：** 每次 add / remove / move / replace / reset 都会在按项钩子之前调用 `OnCollectionChanged<T>`。

## 4. 为什么订阅是惰性的

`_items = []` 这样的字段初始化器直接给 backing field 赋值，因此只存在于 setter 中的订阅永远不会运行。生成的 getter 补上了这一点：

```csharp
global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
```

setter 在替换前解绑旧实例：

```csharp
global::VeloxDev.MVVM.ObservableCollectionTracker.Unsubscribe(old, OnItemsCollectionChanged);
```

去重依据是 `(Method, Target)` 身份，而不是委托引用，因为方法组在每次 getter 读取时都会产生新的委托实例。每个集合的追踪条目存放在 `ConditionalWeakTable` 中，集合被回收时条目随之消失。

**预期结果：** 重复读取 getter 不会增加重复订阅；被替换的集合不再向该视图模型发事件；非 `INotifyCollectionChanged` 的值被静默忽略。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 仅对照 `Base/Analizer.cs`（`MVVMPropertyFactory.GenerateCollectionMembers`）、`MVVM/ObservableCollectionTracker.cs` 与 `Examples/MVVM/WPF/Demo/{MainWindowViewModel.cs, ObservableViewModelBase.cs}` 做了静态核对。
