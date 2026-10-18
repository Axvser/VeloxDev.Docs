# MVVM — Command 生成器

`VeloxDev.Generators.Command` 是把 `[VeloxCommand]` 方法暴露为懒加载命令属性（或泛型访问器）的 Roslyn 增量生成器。源码：`Src/Generators/VeloxDev.Core.Generator/Command.cs`、`Writers/CommandWriter.cs`、`Diagnostics.cs`。

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

1. `Analizer.Filters.Targets` 流式产出每个携带 `VeloxDev.MVVM.VeloxCommandAttribute` 的类。
2. `Analizer.Filters.Resolve` 针对当前编译重新解析符号。
3. `CommandWriter.ReadCommandConfig` 扫描类的方法，为每个 `[VeloxCommand]` 方法建立 `CommandSpec`。
4. 诊断在任何产出**之前**上报。
5. `CanWrite` 为 `CommandConfig.Count > 0`；文件名是 `{类名}_{命名空间下划线化}_Commands.g.cs`。

## 按方法的解析

`ReadCommandConfig` 读取特性实参 —— 先位置参数，再被具名参数覆盖：

| 实参 | 效果 |
| --- | --- |
| `name` | `"Auto"` 由 `method.Name.Replace("Async", "")` 派生；移除所有 `Async` 子串。成员是 `{name}Command`。 |
| `canValidate` | 发出 `canExecute: CanExecute{name}Command` 并声明对应的 `private partial bool`。 |
| `semaphore` | 存为 `Math.Max(1, semaphore)`。 |

`BuildSpec` 随后根据两个独立事实决定形状 —— 返回类型决定值如何变成 `Task`，前导形参列表决定构造方式以及属性是否强类型：

| 返回类型 | 前导形参 | 结果 |
| --- | --- | --- |
| `void` | 0 | `VeloxCommand(Action)` |
| `void` | 1 个 `object?` | `VeloxCommand(Action<object?>)` |
| `void` | 1 个强类型 | 强类型命令（`IVeloxCommand<T, object?>`） |
| `Task` / `Task<T>` | 0 | `VeloxCommand(Func<Task>)`；`Task<T>` 走结果通道工厂 |
| `Task` / `Task<T>` | 1 个 `object?` | 主构造函数或 `CreateTaskOnlyWithParameter`；`Task<T>` 用结果通道 |
| `Task` / `Task<T>` | 1 个强类型 | 强类型构造/工厂；结果通道保留 `TResult` |
| `Task` / `Task<T>` | 2–15 个强类型 | arity 族 `VeloxCommand<T1, …, Tn, TResult>` |
| `ValueTask` / `ValueTask<T>` | 任意 | `.AsTask()` thunk；强类型形状保留结果通道 |
| 任意 | 末尾 `CancellationToken` | token 传给方法体，使该次运行可取消 |
| `Task<T>` | 泛型方法 `M<T>(T value)` | 访问器 `GetMCommand<T>()`，每个封闭 `T` 一条缓存命令 |

`ValueTask` 需要 thunk，因为它没有到 `Task` 的隐式转换且是结构体，无法借助委托协变。产出 `Func<...>` 使生成代码不依赖运行时的 `ValueTask` 入口。

## 诊断 `VELOX_MVVM_CMD001`

**Signature**

```csharp
public static readonly DiagnosticDescriptor UnsupportedCommandSignature = new(
    id: "VELOX_MVVM_CMD001",
    title: "Unsupported [VeloxCommand] signature",
    messageFormat: "'{0}' cannot be turned into a command: {1}",
    category: "VeloxDev.MVVM",
    defaultSeverity: DiagnosticSeverity.Error,
    isEnabledByDefault: true);
```

它是**错误**：生成的文件本来就编不过。没有它时，不受支持的形态会表现为 `*_Commands.g.cs` 里的 `CS1503` / `CS0407`。

| 被拒绝的形态 | 原因片段 |
| --- | --- |
| 类型参数未出现在形参类型中的泛型方法 | `generic method whose type parameters do not appear in its parameter type` |
| 不支持的返回类型 | `a command body must return Task, Task<T>, ValueTask, ValueTask<T> or void` |
| 多于 15 个前导形参 | `the generated command carries at most 15` |
| `void` 且带 `CancellationToken` | `nothing in a synchronous body can observe` |

被拒绝的方法会被**跳过**，类中其余部分照常生成。

## Example

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandSignatureDiagnosticsTests.cs
var (diagnostics, generated) = Run("""
    private Task Good(object? p) { _ = p; return Task.CompletedTask; }
    private void Bad(CancellationToken ct) { _ = ct; }
    """);

Assert.HasCount(1, diagnostics, Describe(diagnostics));
StringAssert.Contains(generated, "GoodCommand");
Assert.DoesNotContain("BadCommand", generated);
```

```csharp
// Source: generated — canValidate 模板
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

强类型形参的关键两行是：

```csharp
// Source: Test — CommandSignatureDiagnosticsTests.cs（断言产物）
// public IVeloxCommand<global::System.String, global::System.Object?> MCommand { ... }
// ... CreateTypedTaskOnlyWithParameter<global::System.String>(command: M, ...)
```

## 说明

- 生成的属性类型是 `IVeloxCommand` 或 `IVeloxCommand<TParam, TResult>`；额外能力经 `VeloxCommandExtensions` 或强类型接口取得。
- 两个生成器共用 `Analizer.Filters.Targets`；只含 `[VeloxProperty]` 成员的类在这里不产出任何东西。
- 面向使用者的契约是特性，见 `01_VeloxCommandAttribute` 页。
