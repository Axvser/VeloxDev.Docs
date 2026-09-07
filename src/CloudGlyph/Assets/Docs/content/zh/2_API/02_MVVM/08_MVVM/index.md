# MVVM — MVVM 生成器

`VeloxDev.Generators.MVVM` 是负责把 `[VeloxProperty]` 成员变成可通知属性的 Roslyn 源生成器。源码：`Src/Generators/VeloxDev.Core.Generator/MVVM.cs`、`Writers/MVVMWriter.cs`、`Base/Analizer.cs`。

```csharp
[Generator(LanguageNames.CSharp)]
public class MVVM : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(Analizer.Filters.FilterContext(context), GenerateSource);
    }
}
```

该生成器随分析器包 `VeloxDev.Core.Generator`（版本 `8.0.0`、`netstandard2.0`、Roslyn `Microsoft.CodeAnalysis.CSharp` 4.3.1）发布，由 `VeloxDev.Core` 传递引用。

## 管线

1. `Analizer.Filters.FilterContext` 收集编译单元中所有 `partial` 类声明。
2. 对每个类，`MVVMWriter` 判断是否需要产出（`CanWrite` 在类携带 `[VeloxProperty]` 字段或 `partial` 属性、或是 Workflow 组件时为真）。
3. 需要产出时，每个类产出一个源文件，命名为 `{ClassName}_{Namespace}_MVVM.g.cs`（命名空间的点替换为 `_`；全局命名空间用 `Global`）。

## 产出的内容

对每个相关类，写入器只生成类尚未提供的成员：

- `PropertyChanging` / `PropertyChanged` 事件、`OnPropertyChanging(string)` / `OnPropertyChanged(string)` 方法，以及（必要时）`INotifyPropertyChanging` / `INotifyPropertyChanged` 接口——除非基类或宿主框架已提供。
- 对每个被标记字段：一个公开属性，其 setter 带等值守卫、触发通知并调用按属性拆分的钩子 `partial void On{Name}Changing(old, value)` / `On{Name}Changed(old, value)`。
- 对每个被标记的 `partial` 属性：一个后备字段加上完整 getter/setter。
- 对集合类型成员（`INotifyCollectionChanged`）：getter 侧经 `ObservableCollectionTracker` 惰性订阅、一个转发到 `OnCollectionChanged<T>` 的私有 `On{Name}CollectionChanged` 处理器，以及 `partial` 钩子 `OnItemAddedTo{Name}` / `OnItemRemovedFrom{Name}` / `OnItemMovedIn{Name}` / `OnItemsResetIn{Name}`。
- 当类属于 Workflow 系统时，还会输出工作流插槽生命周期集成。

## 宿主框架适配

`MVVMWriter.DetectSetterMode` 检查类层级；当识别出宿主 MVVM 框架时，它不自行触发事件，而是把生成的 setter 委托给该框架原生的通知 API：

| 框架 | 检测方式 | 委托调用 |
|---|---|---|
| CommunityToolkit.Mvvm | `[ObservableObject]` / `INotifyPropertyChangedAttribute` | `SetProperty<T>(ref T, T, string)` |
| Prism | 存在 `SetProperty(ref T, T, string)` | `SetProperty<T>(ref T, T, string)` |
| ReactiveUI | 实现 `IReactiveObject` | `RaiseAndSetIfChanged<T>(ref T, T, string)` |
| Caliburn.Micro | 存在 `NotifyOfPropertyChange(string)` | `NotifyOfPropertyChange(string propertyName)` |

面向使用者的契约是特性本身，见 [00_VeloxPropertyAttribute](../00_VeloxPropertyAttribute/index.md)。
