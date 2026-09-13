# MVVM — Command 生成器

`VeloxDev.Generators.Command` 是负责把带 `[VeloxCommand]` 的方法暴露为懒创建 `IVeloxCommand` 属性的 Roslyn 源生成器。源码：`Src/Generators/VeloxDev.Core.Generator/Command.cs`、`Writers/CommandWriter.cs`。

```csharp
[Generator(LanguageNames.CSharp)]
public class Command : IIncrementalGenerator
{
    public void Initialize(IncrementalGeneratorInitializationContext context)
    {
        context.RegisterSourceOutput(Analizer.Filters.FilterContext(context), GenerateSource);
    }
}
```

该生成器随分析器包 `VeloxDev.Core.Generator`（版本 `9.0.0`、`netstandard2.0`）发布，由 `VeloxDev.Core` 传递引用——与 MVVM 生成器在同一个包里（见 [MVVM](../08_MVVM/index.md)）。

## 管线

1. `Analizer.Filters.FilterContext` 收集所有 `partial` 类声明。
2. `CommandWriter.ReadCommandConfig` 扫描类方法，寻找 `[VeloxCommand]`。
3. `CanWrite` 在至少一个方法携带该特性时为真；此后每个此类产出一个源文件 `{ClassName}_{Namespace}_Commands.g.cs`（命名空间的点替换为 `_`）。

## 逐方法解析（`CommandWriter`）

对每个被标记方法，写入器解析：

- `name` — 先位置参数，后命名参数覆盖。`"Auto"`（默认）根据方法名去掉所有 `Async` 子串派生命令名；生成的属性为 `{name}Command`。
- `canValidate` — 为 `true` 时，产出的属性使用 `canExecute: CanExecute{name}Command`，并声明 `private partial bool CanExecute{name}Command(object? parameter)`，由类实现。为 `false` 时使用 `canExecute: _ => true`。
- `semaphore` — 先位置参数，后命名参数覆盖；实际容量为 `Math.Max(1, semaphore)`。

方法签名决定调用哪个 `VeloxCommand` 入口（`ParseConstructorType`）：

| 签名 | 选用的入口 |
|---|---|
| `Task M(object?, CancellationToken)` | 主构造函数 — 委托 `Func<object?, CancellationToken, Task>` |
| `Task M(object?)` | `CreateTaskOnlyWithParameter` — 委托 `Func<object?, Task>` |
| `Task M(CancellationToken)` | `CreateTaskOnlyWithCancellationToken` — 委托 `Func<CancellationToken, Task>` |
| `Task M()`、`void M(object?)`、`void M()` | 匹配的 `VeloxCommand` 构造函数（`Func<Task>` / `Action<object?>` / `Action`） |

## 产出形态

对每个方法，写入器产出一个后备字段与一个懒属性：

```csharp
private VeloxDev.MVVM.IVeloxCommand? _buffer_MinusCommand = null;
public VeloxDev.MVVM.IVeloxCommand MinusCommand
{
    get
    {
        _buffer_MinusCommand ??= new VeloxDev.MVVM.VeloxCommand(
            command: Minus,
            canExecute: CanExecuteMinusCommand,
            semaphore: 1);
        return _buffer_MinusCommand;
    }
}
private partial bool CanExecuteMinusCommand(object? parameter);
```

上面的例子是 `canValidate: true` 模板应用于 `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs` 的 `Minus` 方法。面向使用者的契约是特性本身，见 [VeloxCommandAttribute](../01_VeloxCommandAttribute/index.md)；运行时类型见 [VeloxCommand](../03_VeloxCommand/index.md)。
