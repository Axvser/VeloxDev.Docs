# MVVM — Command 生成器

`VeloxDev.Generators.Command` 是把标注了 `[VeloxCommand]` 的方法暴露为懒加载 `IVeloxCommand` 属性的 Roslyn 增量生成器。源码：`Src/Generators/VeloxDev.Core.Generator/Command.cs`、`Writers/CommandWriter.cs`、`Diagnostics.cs`。

## Class: `Command`

**Signature**

```csharp
[Generator(LanguageNames.CSharp)]
public class Command : IIncrementalGenerator
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
            var writer = new CommandWriter();
            writer.Initialize(syntax, symbol);

            // report diagnostics first: an unsupported signature never reaches the generated file
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

## 流水线

1. `Analizer.Filters.Targets`（`Base/Analizer.cs` 第 107 行）按类型恰好一次地流式产出每个携带 `VeloxDev.MVVM.VeloxCommandAttribute`（`TriggerAttributes` 之一，第 82 行）的类。
2. `Analizer.Filters.Resolve`（第 142 行）针对当前编译重新解析符号。
3. `CommandWriter.ReadCommandConfig`（`Writers/CommandWriter.cs` 第 43 行）扫描类中带 `[VeloxCommand]` 的方法，为每个方法建立一个 `CommandSpec`。
4. `CommandWriter.Diagnostics` 中收集的诊断在任何产出**之前**上报，这样拒绝信息会落在作者自己的代码行上。
5. `CanWrite`（第 243 行）为 `CommandConfig.Count > 0`；文件名是 `{类名}_{命名空间下划线化}_Commands.g.cs`。

## 按方法的解析

`ReadCommandConfig` 解析特性实参 —— 先是位置参数，随后被具名参数覆盖：

| 特性实参 | 效果 |
|---|---|
| `name` | 先位置后具名覆盖。`"Auto"` 由 `methodSymbol.Name.Replace("Async", "")` 派生命令名，因此移除的是**所有** `Async` 子串而不只是后缀。生成的属性是 `{name}Command`。 |
| `canValidate` | 为 `true` 时生成的属性使用 `canExecute: CanExecute{name}Command`，且生成器声明 `private partial bool CanExecute{name}Command(object? parameter)`。为 `false` 时生成的谓词是 `_ => true`。 |
| `semaphore` | 先位置后具名覆盖；存为 `Math.Max(1, semaphore)`。 |

`TryBuildCommandExpression`（第 133 行）随后决定方法如何变成命令。返回类型与形参列表分开判断：

| 返回类型 | 前导形参 | 生成的表达式与构造方式 |
|---|---|---|
| `void` | 0 | method group，`new VeloxCommand(command: M, …)` → `Action` |
| `void` | 1（`object?`） | method group → `Action<object?>` |
| `void` | 1（强类型） | `parameter => M((T)parameter!)` → `Action<object?>` |
| `Task` / `Task<T>` | 0 | method group → `Func<Task>`，若后面跟 token 则为 `CreateTaskOnlyWithCancellationToken` |
| `Task` / `Task<T>` | 1（`object?`） | method group → 主构造函数（带 token）或 `CreateTaskOnlyWithParameter` |
| `Task` / `Task<T>` | 1（强类型） | 同上，但用 `(parameter, ct) => M((T)parameter!, ct)` 或 `parameter => M((T)parameter!)` |
| `ValueTask` / `ValueTask<T>` | 0 | `() => M().AsTask()` 或 `ct => M(ct).AsTask()` |
| `ValueTask` / `ValueTask<T>` | 1 | `parameter => M((T)parameter!).AsTask()` 或 `(parameter, ct) => M((T)parameter!, ct).AsTask()` |

`ValueTask` 需要 thunk，因为它没有到 `Task` 的隐式转换、且是结构体，无法借助委托协变。产出一个 `Func<object?, CancellationToken, Task>` —— 它在四个 TFM 上都存在 —— 使生成的代码不依赖运行时的 `ValueTask` 入口。

## 诊断 `VELOXCMD001`

**Signature**

```csharp
public static readonly DiagnosticDescriptor UnsupportedCommandSignature = new(
    id: "VELOXCMD001",
    title: "Unsupported [VeloxCommand] signature",
    messageFormat: "'{0}' cannot be turned into a command: {1}",
    category: "VeloxDev.MVVM",
    defaultSeverity: DiagnosticSeverity.Error,
    isEnabledByDefault: true);
```

声明于 `VeloxDev.Generators.Diagnostics.UnsupportedCommandSignature`（`Src/Generators/VeloxDev.Core.Generator/Diagnostics.cs`）。它是**错误**而非警告：生成的文件本来就编不过，唯一的问题只是作者看到哪条消息。没有它时，不受支持的形态会表现为 `*_Commands.g.cs` 里的 `CS1503` / `CS0407`，指向作者从未写过的方法组与构造函数。

| 被拒绝的形态 | 原因文本 |
|---|---|
| 泛型方法 | `it is a generic method; the generated command cannot infer its type arguments from a single object? argument…` |
| 不支持的返回类型 | `it returns '…', but a command body must return Task, Task<T>, ValueTask, ValueTask<T> or void` |
| 多于一个前导形参 | `it takes more than one parameter before the optional CancellationToken, and a command carries a single argument…` |
| `void` 且带 `CancellationToken` | `it returns void and takes a CancellationToken, which nothing in a synchronous body can observe…` |

被拒绝的方法会被**跳过**，类中其余部分照常生成。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureDiagnosticsTests.cs, lines 89-99
var (diagnostics, generated) = Run("""
    private Task Good(object? p) { _ = p; return Task.CompletedTask; }
    private void Bad(CancellationToken ct) { _ = ct; }
    """);

Assert.HasCount(1, diagnostics, Describe(diagnostics));
StringAssert.Contains(generated, "GoodCommand", "one bad method must not take the good one down with it");
Assert.DoesNotContain("BadCommand", generated);
```

```csharp
// Source: Generated — obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Command/CounterViewModel_QuickStart_Mvvm_Commands.g.cs
private global::VeloxDev.MVVM.IVeloxCommand? _buffer_DecrementCommand = null;
public global::VeloxDev.MVVM.IVeloxCommand DecrementCommand
{
    get
    {
        _buffer_DecrementCommand ??= new global::VeloxDev.MVVM.VeloxCommand(
            command: Decrement,
            canExecute: CanExecuteDecrementCommand,
            semaphore: 1);
        return _buffer_DecrementCommand;
    }
}
private partial bool CanExecuteDecrementCommand(object? parameter);
```

## Notes

- 生成的属性类型是 `IVeloxCommand`，所以它的额外能力经 `VeloxCommandExtensions` 取得。
- 两个生成器共用 `Analizer.Filters.Targets`；只含 `[VeloxProperty]` 成员的类在这里不产出任何东西。
- 上面的生成片段是 `canValidate: true` 模板应用于快速开始完整代码程序的 `Decrement` 方法；同一模板为 `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs` 产出 `MinusCommand`。面向使用者的契约是特性，见 `01_VeloxCommandAttribute` 页；运行时类型是 `VeloxCommand`。
