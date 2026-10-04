# MVVM — MVVM 生成器

`VeloxDev.Generators.MVVM` 是把 `[VeloxProperty]` 成员变成可通知属性的 Roslyn 增量生成器。源码：`Src/Generators/VeloxDev.Core.Generator/MVVM.cs`、`Writers/MVVMWriter.cs`、`Base/Analizer.cs`、`Base/ICodeWriter.cs`、`Writers/WriterBase.cs`。

## Class: `MVVM`

**Signature**

```csharp
[Generator(LanguageNames.CSharp)]
public class MVVM : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(
            Analizer.Filters.Targets(context).Combine(context.CompilationProvider),
            GenerateSource);
    }

    public void GenerateSource(SourceProductionContext context, (ImmutableArray<Analizer.Filters.GeneratorTarget> Targets, Compilation Compilation) input)
    {
        foreach (var (syntax, symbol) in Analizer.Filters.Resolve(input.Targets, input.Compilation))
        {
            var writer = new MVVMWriter();
            writer.Initialize(syntax, symbol);

            if (writer.CanWrite())
            {
                context.AddSource(
                    writer.GetFileName(),
                    SourceText.From(writer.Write(), Encoding.UTF8));
            }
        }
    }
}
```

生成器随分析器包 `VeloxDev.Core.Generator`（`netstandard2.0`，Roslyn `Microsoft.CodeAnalysis.CSharp` 4.3.1）发布，由 `VeloxDev.Core` 传递引用。

##### Methods

| 成员 | 签名 | 说明 |
|---|---|---|
| `Initialize` | `void Initialize(IncrementalGeneratorInitializationContext context)` | 注册组合后的 provider。 |
| `GenerateSource` | `void GenerateSource(SourceProductionContext context, (ImmutableArray<GeneratorTarget> Targets, Compilation Compilation) input)` | 解析每个目标，并在 writer 表示有内容可产出时添加一个源文件。 |

## 流水线

1. **`Analizer.Filters.Targets(context)`**（`Base/Analizer.cs` 第 107 行）为 `TriggerAttributes`（第 82 行）中的每一项注册一个 `ForAttributeWithMetadataName` 语法 provider —— `VeloxDev.MVVM.VeloxPropertyAttribute` 是其中之一 —— 并拼接成一个去重后的 `ImmutableArray<GeneratorTarget>`。`GeneratorTarget` 刻意不携带任何 `ISymbol`：转换的输出按语法节点缓存，捕获的符号会过期。只有携带触发特性的类才会到达 writer。
2. **`Analizer.Filters.Resolve(targets, compilation)`**（第 142 行）针对**当前**编译重新解析符号，返回 `(ClassDeclarationSyntax, INamedTypeSymbol)` 对，并跳过已不属于该编译的语法树。
3. **`MVVMWriter.Initialize`**（`Writers/MVVMWriter.cs`）读取该类：`ConfigurePropertyNotificationInfrastructure`（第 198 行）、针对 `[VeloxProperty]` 字段的 `ReadMVVMConfig`（第 91 行）、针对 `[VeloxProperty]` partial 属性的 `ReadAutoProperties`（第 117 行）。`DetectSetterMode`（第 42 行）决定生成的 setter 调用哪套通知 API。
4. **`CanWrite`**（第 845 行）为 `MVVMProperties.Count > 0 || AutoProperties.Count > 0 || IsWorkflowComponent`。
5. **`GetFileName`**（第 847 行）返回 `{类名}_{命名空间下划线化}_MVVM.g.cs`。

## 产出内容

对每个相关类，writer 只生成该类尚未提供的成员：

- `PropertyChanging` / `PropertyChanged` 事件、`OnPropertyChanging(string)` / `OnPropertyChanged(string)`，并在无人提供时补上 `INotifyPropertyChanging` / `INotifyPropertyChanged` 接口。
- 对每个被标注字段：一个公开属性，其 setter 带守卫、触发通知并调用 `partial void On{名称}Changing(old, value)` / `On{名称}Changed(old, value)` 钩子（`MVVMPropertyFactory.GetSetterBodyLines`，`Base/Analizer.cs` 第 466 行；字段命名来自 `MVVMFieldAnalizer.GetPropertyNameFromFieldName`，第 256 行）。
- 对每个被标注的 `partial` 属性：一个后备字段以及完整的 getter / setter。
- 对集合类型成员（`INotifyCollectionChanged`）：getter 侧经 `ObservableCollectionTracker` 的懒加载订阅、转发到 `OnCollectionChanged<T>` 的私有 `On{名称}CollectionChanged` 处理器，以及 `partial` 钩子 `OnItemAddedTo{名称}` / `OnItemRemovedFrom{名称}` / `OnItemMovedIn{名称}` / `OnItemsResetIn{名称}`（`MVVMPropertyFactory.GenerateCollectionMembers`，第 754 行）。
- 当该类属于 Workflow 系统时，还生成工作流组件生命周期集成。

两个生成器共用**同一个** `Filters.Targets` provider，所以 MVVM 生成器也会看到只携带 `[VeloxCommand]` 的类 —— 它对那些类无内容可写，`CanWrite` 返回 `false`。

## 宿主框架适配

`MVVMWriter.DetectSetterMode` 检查类层级，在识别到宿主 MVVM 框架时，让生成的 setter 委托给该框架的原生通知 API，而不是自己触发事件：

| 框架 | 识别方式 | 委托调用 |
|---|---|---|
| CommunityToolkit.Mvvm | `[ObservableObject]` / `INotifyPropertyChangedAttribute` | `SetProperty<T>(ref T, T, string)` |
| Prism | 存在 `SetProperty(ref T, T, string)` | `SetProperty<T>(ref T, T, string)` |
| ReactiveUI | 实现 `IReactiveObject` | `RaiseAndSetIfChanged<T>(ref T, T, string)` |
| Caliburn.Micro | 存在 `NotifyOfPropertyChange(string)` | `NotifyOfPropertyChange(string propertyName)` |

面向使用者的契约是那个特性，记录在 `00_VeloxPropertyAttribute` 页。

## Example —— 真实类产出的文件

```csharp
// Source: Generated — obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/CounterViewModel_QuickStart_Mvvm_MVVM.g.cs
namespace QuickStart.Mvvm;

public partial class CounterViewModel : global::System.ComponentModel.INotifyPropertyChanging, global::System.ComponentModel.INotifyPropertyChanged
{
public event global::System.ComponentModel.PropertyChangingEventHandler? PropertyChanging;
public event global::System.ComponentModel.PropertyChangedEventHandler? PropertyChanged;
public virtual void OnPropertyChanging(string propertyName)
{
    PropertyChanging?.Invoke(this, new global::System.ComponentModel.PropertyChangingEventArgs(propertyName));
}
public virtual void OnPropertyChanged(string propertyName)
{
    PropertyChanged?.Invoke(this, new global::System.ComponentModel.PropertyChangedEventArgs(propertyName));
}
    protected virtual void OnCollectionChanged<T>(string propertyName, global::System.Collections.Specialized.NotifyCollectionChangedEventArgs e, global::System.Collections.Generic.IEnumerable<T>? oldItems, global::System.Collections.Generic.IEnumerable<T>? newItems)
    {
    }
    // then: one property plus its partial hooks per [VeloxProperty] member
}
```
