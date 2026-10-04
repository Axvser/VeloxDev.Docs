# MVVM — 观察集合变化

当 `[VeloxProperty]` 成员的类型实现了 `INotifyCollectionChanged`（例如 `ObservableCollection<T>` 以及大多数集合视图模型），生成器会自动把 `CollectionChanged` 接到你的钩子上 —— 既包括集合**内部**条目发生变化，也包括整个集合实例被**替换**。

## 1. 声明集合属性

特性不变，变的是类型：

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

**预期结果：** 生成 `public ObservableCollection<string> Items`。`Items.Add(...)` 与 `Items = [...]` 都能被观察到 —— 第 4 节解释为什么只靠字段初始化器会被漏掉。

## 2. 生成的成员

对于名为 `Items`、条目类型为 `string` 的属性，生成器产出如下钩子面（逐字取自真实构建）：

```csharp
partial void OnItemsChanging(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);
partial void OnItemsChanged(ObservableCollection<System.String> oldValue, ObservableCollection<System.String> newValue);

partial void OnItemAddedToItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemRemovedFromItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemMovedInItems(System.Collections.Generic.IEnumerable<System.String> items);
partial void OnItemsResetInItems();
```

`OnItemsChanging` / `OnItemsChanged` 在整个集合实例经属性 setter 被替换时触发。四个按条目钩子由生成的私有处理器 `OnItemsCollectionChanged` 按底层事件的 `NotifyCollectionChangedAction` 分派：

| `NotifyCollectionChangedAction` | 触发的钩子 |
|---|---|
| `Add` | `OnItemAddedToItems(e.NewItems)` |
| `Remove` | `OnItemRemovedFromItems(e.OldItems)` |
| `Replace` | 先 `OnItemRemovedFromItems(e.OldItems)`，再 `OnItemAddedToItems(e.NewItems)` |
| `Move` | `OnItemMovedInItems(e.NewItems)` |
| `Reset` | `OnItemsResetInItems()` |

在类的另一半实现其中任意一个即可。WPF 与 Avalonia 演示（`Examples/MVVM/*/.../MainWindowViewModel.cs`）为它们的 `Items` 集合实现了全部四个。

**预期结果：** `Items.Add("x")` 以新增条目调用 `OnItemAddedToItems`；`Items.Clear()` 调用 `OnItemsResetInItems`；替换整个集合实例会调用 `OnItemsChanged`，随后新内容经 `OnItemAddedToItems` 批量加入，旧内容在此之前经 `OnItemRemovedFromItems` 批量移除。

## 3. 可重写的 `OnCollectionChanged<T>`

每个集合事件还会汇聚到一个重写点，且在四个按条目钩子**之前**触发。当基类没有提供时，生成器会生成如下代码（这里展示的是裸 `partial class` 的生成结果）：

```csharp
protected virtual void OnCollectionChanged<T>(
    string propertyName,
    global::System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
    global::System.Collections.Generic.IEnumerable<T>? oldItems,
    global::System.Collections.Generic.IEnumerable<T>? newItems)
{
}
```

如果基类已经声明了它则直接复用 —— 演示就在自己的 `ObservableViewModelBase` 中重写：

```csharp
protected override void OnCollectionChanged<T>(
    string propertyName,
    System.Collections.Specialized.NotifyCollectionChangedEventArgs e,
    System.Collections.Generic.IEnumerable<T>? oldItems,
    System.Collections.Generic.IEnumerable<T>? newItems)
{
    System.Console.WriteLine($"{propertyName}: {e.Action}");
}
```

**预期结果：** 每次增/删/移/替换/重置，除了触发按条目钩子外，还会打印一行 `OnCollectionChanged<T>`。

## 4. 订阅为何是懒加载的（`ObservableCollectionTracker`）

像 `_items = []` 这样的字段初始化器会**直接**给后备字段赋值，绕过生成的 setter，因此只写在 setter 里的订阅步骤对它永不执行。`VeloxDev.MVVM.ObservableCollectionTracker` 补上了这个缺口：

- 生成的 **getter** 在每次访问时调用 `ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged)`，且只订阅一次；
- 生成的 **setter** 在替换前对旧实例调用 `Unsubscribe(old, OnItemsCollectionChanged)`，因此不会有处理器泄漏到被丢弃的集合上。

上面属性的生成 getter 逐字如下：

```csharp
public System.Collections.ObjectModel.ObservableCollection<System.String> Items
{
    get
    {
        global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
        return this._items;
    }
    set
    {
        if (global::System.Object.Equals(this._items, value)) return;
        var old = this._items;
        OnPropertyChanging(nameof(Items));
        OnItemsChanging(old, value);
        global::VeloxDev.MVVM.ObservableCollectionTracker.Unsubscribe(old, OnItemsCollectionChanged);
        this._items = value;
        global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(value, OnItemsCollectionChanged);
        OnItemsChanged(old, value);
        OnPropertyChanged(nameof(Items));
    }
}
```

去重按 `(Method, Target)` 身份而非委托引用进行，因为每次 getter 读取时 method group 都会产生新的委托实例；按引用比较会导致每次读取都重复订阅，让调用列表无界增长。追踪条目存放在 `ConditionalWeakTable` 中，因此集合被回收时条目一并消失。

**预期结果：** 在任意一次 getter 访问之后加入的条目都会触发钩子，即使该集合来自字段初始化器；重复读取 getter 不会产生重复订阅；被替换掉的集合不再为该视图模型触发事件。

## 运行声明

- ✅ 2026-10-01 实际构建并运行过。上面这个 `Items` 属性 —— 包括懒加载的 `= []` 初始化器与构造函数里的 `Items.Add("ready")` —— 在一个临时控制台项目中用 `dotnet build -c Debug -p:EmitCompilerGeneratedFiles=true` 编译，并用 `dotnet run -c Debug` 运行（该项目引用 `VeloxDev.Core` 与生成器）。录制输出，展示了在字段初始化器绕过 setter 之后发生的变更依然触发了钩子：

  ```text
  [collection] added: ready
  initial: Count=0, CanExecute(Decrement)=False
  Items: ready
  ```

- 第 4 节的生成属性与第 2 节的钩子声明逐字抄自 `obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/CounterViewModel_QuickStart_Mvvm_MVVM.g.cs`。动作表中的 `Replace` 与 `Reset` 两行本次未单独执行；它们转录自同一文件中生成的 `OnItemsCollectionChanged` switch。
