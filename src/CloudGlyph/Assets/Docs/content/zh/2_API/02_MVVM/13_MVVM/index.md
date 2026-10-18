# MVVM — MVVM 生成器

`VeloxDev.Generators.MVVM` 是把 `[VeloxProperty]` 成员变成变更通知属性的 Roslyn 增量生成器。源码：`Src/Generators/VeloxDev.Core.Generator/MVVM.cs`、`Writers/MVVMWriter.cs`、`Base/Analizer.cs`、`Base/ICodeWriter.cs`、`Writers/WriterBase.cs`。

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

            foreach (var diagnostic in writer.Diagnostics)
            {
                context.ReportDiagnostic(diagnostic);
            }

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

生成器随分析器包 `VeloxDev.Core.Generator`（`netstandard2.0`、`Microsoft.CodeAnalysis.CSharp` 4.8.0）发布，由 `VeloxDev.Core` 引用。

##### Methods

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Initialize` | `void Initialize(IncrementalGeneratorInitializationContext context)` | 注册组合后的提供器。 |
| `GenerateSource` | `void GenerateSource(SourceProductionContext, (ImmutableArray<GeneratorTarget>, Compilation))` | 先上报诊断，再解析每个目标，并在写入器有产出时添加一个源文件。 |

## 流水线

1. **`Analizer.Filters.Targets`** 为 `TriggerAttributes` 中的每一项注册一个 `ForAttributeWithMetadataName` 提供器 —— 其中包括 `VeloxDev.MVVM.VeloxPropertyAttribute` —— 并按类型键去重。`GeneratorTarget` 不携带 `ISymbol`，因此缓存变换不会持有过期符号。
2. **`Analizer.Filters.Resolve`** 针对当前编译重新解析每个符号。
3. **`MVVMWriter.Initialize`** 调用 `ConfigurePropertyNotificationInfrastructure`、`ReadMVVMConfig`（字段）、`ReadAutoProperties`（`partial` 属性）与 `DetectSetterMode`。
4. **`CanWrite`** 为 `MVVMProperties.Count > 0 || AutoProperties.Count > 0 || IsWorkflowComponent`。
5. **`GetFileName`** 返回 `{类名}_{命名空间下划线化}_MVVM.g.cs`。

## 产出内容

只生成类中缺少的成员：

- `PropertyChanging` / `PropertyChanged`、`OnPropertyChanging(string)` / `OnPropertyChanged(string)`，以及无人提供时的 `INotifyPropertyChanging` / `INotifyPropertyChanged`。
- 每个被标注字段：带守卫 setter 的公开属性，以及 `partial void On{Name}Changing(old, new)` / `On{Name}Changed(old, new)`。
- 每个被标注的 `partial` 属性：backing field（除非已存在可访问的约定字段）与访问器，并保留声明的可访问性。
- 集合类型成员：getter 侧的 `ObservableCollectionTracker.EnsureSubscribed`、setter 侧的 `Unsubscribe`、私有 `On{Name}CollectionChanged` 处理器，以及 `OnItemAddedTo{Name}` / `OnItemRemovedFrom{Name}` / `OnItemMovedIn{Name}` / `OnItemsResetIn{Name}`。
- 类属于 Workflow 系统时的组件生命周期集成。

## 诊断

| Id | 级别 | 条件 |
| --- | --- | --- |
| `VELOX_MVVM_PROP001` | Error | 属性声明冲突（派生名重复，或已有字段无法支撑该属性） |
| `VELOX_MVVM_PROP002` | Warning | 字段名推不出合法标识符 |
| `VELOX_MVVM_PROP003` | Warning | 被标注的属性不是 `partial` |
| `VELOX_LANGVERSION001` | Warning | 项目的 `LangVersion` 低于生成代码所需 |

无论是否写出文件都会上报诊断，因此被拒绝的声明不会静默消失。

## 宿主框架适配

`MVVMWriter.DetectSetterMode` 检查类层次结构，在识别到宿主框架时把生成的 setter 委托给它的通知器：

| 框架 | 检测方式 | 委托调用 |
| --- | --- | --- |
| CommunityToolkit.Mvvm | `[ObservableObject]` / `INotifyPropertyChangedAttribute` | `SetProperty<T>(ref T, T, string)` |
| Prism | 带 `SetProperty(ref T, T, string)` 的基类 | `SetProperty<T>(ref T, T, string)` |
| ReactiveUI | 实现 `IReactiveObject` | `RaiseAndSetIfChanged<T>(ref T, T, string)` |
| Caliburn.Micro | 存在 `NotifyOfPropertyChange(string)` | `NotifyOfPropertyChange(string propertyName)` |

## Example — 一个真实类的生成文件

```csharp
// Source: generated — {类名}_{命名空间}_MVVM.g.cs
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

    // 之后：每个 [VeloxProperty] 成员一个属性及其 partial 钩子
}
```
