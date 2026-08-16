# MVVM — `ObservableCollectionTracker`

弱引用订阅辅助类，确保即使在字段直接初始化（`= []`）而绕过生成的 setter 时，`CollectionChanged` 仍保持订阅。

**签名**（`Src/Core/VeloxDev.Core/MVVM/ObservableCollectionTracker.cs`，第 15-56 行）：

```csharp
public static void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)
public static void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)
```

- **备注：** 使用以集合身份为键的 `ConditionalWeakTable<object, Entry>`，因此当集合被回收时条目随之消失 — 无泄漏。处理器按 `(Method, Target)` 身份去重（`MethodTargetEqualityComparer`，第 96-114 行），而非按委托引用：生成的 getter 传的是方法组（例如 `OnItemsCollectionChanged`），每次访问 getter 都会产生新的委托实例；按引用比较会在每次访问时重复订阅并让事件调用列表无限增长。生成的 getter 每次访问都调用 `EnsureSubscribed`，但真正订阅只发生一次（`Base/Analizer.cs`，`GenerateGetter`，第 444-464 行）。
- **示例：** 示例中的 `[VeloxProperty] private ObservableCollection<string> _items = [];`（`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 30 行）依赖 getter 侧的 `EnsureSubscribed` 调用，因为初始化器直接给字段赋值。

## 命名空间 `VeloxDev.Generators`

源生成器内部实现（程序集 `VeloxDev.Core.Generator`，包版本 `7.0.0`，目标 `netstandard2.0`，Roslyn `Microsoft.CodeAnalysis.CSharp` 4.3.1）。

| 项目 | 详情 |
|---|---|
| 包 | `VeloxDev.Core.Generator` `7.0.0`，由 `VeloxDev.Core` 传递引用 |
| 程序集命名空间 | `VeloxDev.Generators` |
| MVVM 生成器 | `VeloxDev.Generators.MVVM : IIncrementalGenerator`（`MVVM.cs`，第 12-13 行） |
| 命令生成器 | `VeloxDev.Generators.Command : IIncrementalGenerator`（`Command.cs`，第 12-13 行） |
| 类过滤 | `Analizer.Filters.FilterContext` — 仅 `partial` 类声明（`Base/Analizer.cs`，第 13-24 行） |
| 属性写入器 | `Writers/MVVMWriter.cs` + `Base/Analizer.cs`（`MVVMPropertyFactory`，第 208-729 行） |
| 命令写入器 | `Writers/CommandWriter.cs` |
| MVVM 输出文件名 | `{ClassName}_{Namespace}_MVVM.g.cs`（命名空间的点替换为 `_`；全局命名空间为 `Global`）— `MVVMWriter.cs`，第 847-854 行 |
| 命令输出文件名 | `{ClassName}_{Namespace}_Commands.g.cs` — `CommandWriter.cs`，第 121-130 行 |
