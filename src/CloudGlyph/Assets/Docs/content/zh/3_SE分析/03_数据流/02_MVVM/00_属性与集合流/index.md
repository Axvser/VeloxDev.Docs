# 数据流 — 属性与集合

标量属性路径与集合路径形状相同：生成器在编译期发出骨架，setter 在运行期驱动它。集合路径额外加入惰性订阅，使字段初始化器（`= []`）无法让 `CollectionChanged` 失去观察。

## (a) 生成器输出 → INPC 流

```plantuml
@startuml
!theme plain

participant "源生成器\nVeloxDev.Generators.MVVM" as Gen
participant "MVVM partial\nCounterViewModel_..._MVVM.g.cs" as GVM
participant "命令体\n(Increment 方法)" as Body
participant "绑定\nWPF / Avalonia" as Bind

== 编译期：生成器输出 ==
Gen -> GVM: MVVMWriter 发出 Count 属性；OnPropertyChanging /\nOnPropertyChanged 方法；OnCountChanging / OnCountChanged partial
note right of GVM: 与手写 partial 合并为同一个类型

== 运行期：生成的 setter 驱动 INPC ==
Body -> GVM: Count = newValue
activate GVM
GVM -> GVM: 相等性守卫（未变化则提前返回）
GVM -> GVM: OnPropertyChanging(nameof(Count)) -> PropertyChanging
GVM -> GVM: OnCountChanging(old, value)（用户 partial 钩子）
GVM -> GVM: 给 backing field this._count 赋值
GVM -> GVM: OnCountChanged(old, value)（用户 partial 钩子）
GVM -> Bind: OnPropertyChanged(nameof(Count)) 触发 PropertyChanged
Bind -> Bind: 重新读取 Count，刷新绑定控件
GVM --> Body
deactivate GVM
@enduml
```

> 源码：setter 形状由 `MVVMPropertyFactory.GetSetterBodyLines`（`Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`）产出。

```csharp
// Source: Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs（Default setter 模式）
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
```

## (b) 集合流：初始化器 → getter 订阅 → 按动作钩子

关键一步是构造函数里的第一次 `Items.Add("ready")`。字段初始化器直接给 `this._items` 赋值，setter 从未运行；订阅之所以存在，只是因为通往 `Add` 的路上读取了 **getter**。

```plantuml
@startuml
!theme plain

participant "构造函数" as Ctor
participant "生成的 getter\nItems" as Getter
participant "ObservableCollectionTracker" as Tracker
participant "ObservableCollection\n<string>" as Coll
participant "生成的处理器\nOnItemsCollectionChanged" as Handler
participant "用户钩子\nOnItemAddedToItems" as Hooks

Ctor -> Getter: Items.Add("ready")
activate Getter
Getter -> Tracker: EnsureSubscribed(this._items, OnItemsCollectionChanged)
activate Tracker
Tracker -> Tracker: ConditionalWeakTable.GetOrCreateValue(collection)
Tracker -> Tracker: Entry.TryAdd(handler) -> 按 (Method, Target) 去重
Tracker -> Coll: CollectionChanged += handler
Tracker --> Getter
deactivate Tracker
Getter --> Ctor: this._items
deactivate Getter

Ctor -> Coll: Add("ready")
activate Coll
Coll -> Handler: CollectionChanged(sender, e) [Action = Add]
activate Handler
Handler -> Handler: OnCollectionChanged(nameof(Items), e, oldItems, newItems)
Handler -> Hooks: OnItemAddedToItems(枚举 NewItems)
Hooks --> Handler
Handler --> Coll
deactivate Handler
Coll --> Ctor
deactivate Coll
@enduml
```

> 源码：`MVVMPropertyFactory.GenerateCollectionMembers`（`Base/Analizer.cs`）；tracker 行为 —— `Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`。

```csharp
// Source: Base/Analizer.cs —— 生成的集合 getter
get
{
    global::VeloxDev.MVVM.ObservableCollectionTracker.EnsureSubscribed(this._items, OnItemsCollectionChanged);
    return this._items;
}
```

## (c) 替换整个集合

替换是 `Unsubscribe` 发挥作用的场景：没有它，被丢弃的集合会继续持有指回本视图模型的处理器。

```plantuml
@startuml
!theme plain

participant "代码" as Code
participant "生成的 setter\nItems" as Setter
participant "ObservableCollectionTracker" as Tracker
participant "旧集合" as Old
participant "新集合" as New
participant "用户钩子" as Hooks

Code -> Setter: Items = newList
activate Setter
Setter -> Setter: Object.Equals(this._items, value) 守卫
Setter -> Setter: OnPropertyChanging(nameof(Items))
Setter -> Setter: OnItemsChanging(old, value)
Setter -> Tracker: Unsubscribe(old, OnItemsCollectionChanged)
activate Tracker
Tracker -> Old: CollectionChanged -= handler
Tracker -> Tracker: Entry.Remove(handler)（记录保留）
Tracker --> Setter
deactivate Tracker
Setter -> Hooks: OnItemRemovedFromItems(枚举 old)
Setter -> Setter: this._items = value
Setter -> Tracker: EnsureSubscribed(value, OnItemsCollectionChanged)
activate Tracker
Tracker -> New: CollectionChanged += handler
Tracker --> Setter
deactivate Tracker
Setter -> Hooks: OnItemAddedToItems(枚举 new)
Setter -> Setter: OnItemsChanged(old, value)
Setter -> Setter: OnPropertyChanged(nameof(Items))
Setter --> Code
deactivate Setter
@enduml
```

> 源码：`MVVMPropertyFactory.GetSetterBodyLines` 与 `GenerateCollectionMembers`（`Base/Analizer.cs`）；`Unsubscribe` —— `ObservableCollectionTracker.cs`。

## 按动作分发

生成的 `OnItemsCollectionChanged` 先调用 `OnCollectionChanged<T>`，再把 `NotifyCollectionChangedAction` 映射到用户钩子：

```csharp
// Source: Base/Analizer.cs —— GenerateCollectionMembers
var oldItems = e.OldItems is null ? null : EnumerateItemsItems(e.OldItems);
var newItems = e.NewItems is null ? null : EnumerateItemsItems(e.NewItems);
OnCollectionChanged(nameof(Items), e, oldItems, newItems);
switch (e.Action)
{
    case NotifyCollectionChangedAction.Add when e.NewItems is not null:
        OnItemAddedToItems(EnumerateItemsItems(e.NewItems));
        break;
    case NotifyCollectionChangedAction.Remove when e.OldItems is not null:
        OnItemRemovedFromItems(EnumerateItemsItems(e.OldItems));
        break;
    case NotifyCollectionChangedAction.Replace:
        if (e.OldItems is not null)
        {
            OnItemRemovedFromItems(EnumerateItemsItems(e.OldItems));
        }
        if (e.NewItems is not null)
        {
            OnItemAddedToItems(EnumerateItemsItems(e.NewItems));
        }
        break;
    case NotifyCollectionChangedAction.Move when e.NewItems is not null:
        OnItemMovedInItems(EnumerateItemsItems(e.NewItems));
        break;
    case NotifyCollectionChangedAction.Reset:
        OnItemsResetInItems();
        break;
}
```

## 错误与边界路径

| 路径 | 行为 |
| --- | --- |
| 值未变化 | 相等性守卫在任何通知或钩子之前返回。 |
| 集合不实现 `INotifyCollectionChanged` | `EnsureSubscribed` / `Unsubscribe` 立即返回。 |
| `null` 集合 | 同样提前返回；不抛异常。 |
| 处理器是新的方法组委托 | 按 `(Method, Target)` 去重，因此调用列表不会增长。 |
| 集合被垃圾回收 | 它的 `ConditionalWeakTable` 条目随之消失 —— 无泄漏。 |
| 处理器抛异常 | 集合处理器是普通 .NET 事件订阅者，不受 tracker 保护。 |
