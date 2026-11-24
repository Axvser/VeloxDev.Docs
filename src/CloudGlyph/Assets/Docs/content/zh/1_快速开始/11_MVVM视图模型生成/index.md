# MVVM 视图模型生成

编写一个控制台程序，属性、命令与集合钩子全部由特性生成。生成器是 Roslyn 分析器：运行时不反射，首次构建后这些成员就是普通的 C# 代码。

## 1. 前置条件

- **`VeloxDev.Core` 支持的目标框架**（声明于 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`）：`netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`。本示例使用 `net8.0`；在 `netstandard2.0` 上让命令体返回 `ValueTask` 还需额外引用 `System.Threading.Tasks.Extensions`。
- **`VeloxDev.Core.Generator`** 是目标为 `netstandard2.0` 的分析器，运行在 C# 编译器内部。它不是运行时依赖。NuGet 引用 Core 会带上分析器；`ProjectReference` 不会，所以该工程要把它作为分析器引用。示例显式安装生成器包，是为了构建期 Roslyn 检查。
- .NET SDK 8.0 或更高。无需任何服务。

## 2. 安装/引入依赖

```text
dotnet new console -n MvvmQuickStart
cd MvvmQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 命令退出码为 0，`MvvmQuickStart.csproj` 中出现两个包的 `PackageReference`。首次构建后生成的成员会出现在 IntelliSense 中；若想检查 `obj/` 下的 `*_MVVM.g.cs` 与 `*_Command.g.cs`，请设置 `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>`。

## 3. 基础配置/注册

类只需带 `partial` 修饰符。通知接口、背后的属性、命令对象与集合管线都由生成器补齐。

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "Untitled";
    [VeloxProperty] private int _priority = 1;
    [VeloxProperty] private ObservableCollection<string> _tags = new();

    partial void OnPriorityChanged(int oldValue, int newValue)
        => System.Console.WriteLine($"[property] priority {oldValue} -> {newValue}");

    partial void OnItemAddedToTags(IEnumerable<string> tags)
        => System.Console.WriteLine($"[collection] added {string.Join(", ", tags)}");

    [VeloxCommand(canValidate: true)]
    private void Promote() => Priority++;

    private partial bool CanExecutePromoteCommand(object? parameter) => Priority < 3;
}
```

**预期结果：** 该类以 `INotifyPropertyChanged` 编译；尽管只写了带下划线的字段，`Title`、`Priority`、`Tags` 与 `PromoteCommand` 都已可用。`_priority` 去掉下划线并把首字母大写后映射为 `Priority`。

## 4. 核心用法（逐步构建）

### 4.1 属性与回调

`[VeloxProperty]` 可用在字段或 `partial` 属性上。生成的 setter 比较新旧值，触发 `PropertyChanging`/`PropertyChanged`，并以新旧两个值调用 `On{Name}Changing` / `On{Name}Changed` 分部方法。字段初始化器照常生效，因此默认值写在字段上即可。

```csharp
var note = new NoteViewModel();
note.Title = "Ship the wiki";   // 生成的 setter
System.Console.WriteLine(note.Priority);
```

**预期结果：** 赋值编译到生成的属性上；代码里没有任何手写的 `SetProperty` 调用。

### 4.2 命令

命令成员名是方法名删除所有 `Async` 出现处后加 `Command`：`Promote` 变成 `PromoteCommand`，`SaveAsync` 也会变成 `SaveCommand`。方法体可返回 `void`、`Task`、`Task<T>`、`ValueTask` 或 `ValueTask<T>`，末尾可带一个 `CancellationToken`。

```csharp
if (note.PromoteCommand.CanExecute(null))
{
    note.PromoteCommand.Execute(null);
}
```

`canValidate: true` 会让生成器声明 `private partial bool CanExecutePromoteCommand(...)`；不实现它是编译错误，而不是一条静默恒可执行的命令。没有前导形参的方法，其校验器收到单个 `object?`。

**预期结果：** 当 `Priority < 3` 时 `CanExecute(null)` 为 `true`；执行后触发属性回调。

### 4.3 集合钩子

对 `ObservableCollection<T>` 属性，生成的 getter 会惰性订阅，并提供四个分部钩子：`OnItemAddedTo{Name}`、`OnItemRemovedFrom{Name}`、`OnItemMovedIn{Name}` 与 `OnItemsResetIn{Name}`。通用的 `OnCollectionChanged<T>` 能看到每一次动作及其新旧项。

```csharp
note.Tags.Add("docs");   // getter 先订阅，随后 Add 触发 OnItemAddedToTags
```

**预期结果：** `OnItemAddedToTags` 的实现打印 `[collection] added docs`。

### 4.4 等待结果、中断与刷新可执行性

`IVeloxCommand` 提供 `Lock`、`Unlock`、`Notify`、`Interrupt`、`Clear`、`Continue` 及其可等待版本；当校验器读取的状态变化后，`Notify()` 会触发 `CanExecuteChanged`。有返回值的命令暴露为 `IVeloxCommand<TParam, TResult>`，其 `ExecuteAsync` 可被 `await`。

```csharp
note.PromoteCommand.Notify();          // 重新评估 CanExecute
await note.PromoteCommand.InterruptAsync();
```

**预期结果：** 界面（或控制台对 `CanExecute` 的检查）看到新的可执行性；中断会在命令的 `Canceled` 事件上报 `Canceled`。

## 5. 验证

用 `dotnet run` 运行下方完整程序。控制台应先出现集合钩子，再出现两次属性变更，最终优先级为 3。第三次 `CanExecute` 必须为 `False`，证明校验器已接上。

```text
[collection] added docs
Ship the wiki / priority 1 / tags 1
can execute at 1: True
[property] priority 1 -> 2
can execute at 2: True
[property] priority 2 -> 3
can execute at 3: False
final priority: 3
```

## 6. 完整代码

用以下内容替换 `Program.cs`。顶层语句在前，分部类在后。

```csharp
using System;
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

var note = new NoteViewModel { Title = "Ship the wiki", Priority = 1 };

note.Tags.Add("docs");
Console.WriteLine($"{note.Title} / priority {note.Priority} / tags {note.Tags.Count}");

for (var i = 0; i < 3; i++)
{
    Console.WriteLine($"can execute at {note.Priority}: {note.PromoteCommand.CanExecute(null)}");
    if (note.PromoteCommand.CanExecute(null))
    {
        note.PromoteCommand.Execute(null);
    }
}

Console.WriteLine($"final priority: {note.Priority}");

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "Untitled";
    [VeloxProperty] private int _priority = 1;
    [VeloxProperty] private ObservableCollection<string> _tags = new();

    partial void OnPriorityChanged(int oldValue, int newValue)
        => Console.WriteLine($"[property] priority {oldValue} -> {newValue}");

    partial void OnItemAddedToTags(IEnumerable<string> tags)
        => Console.WriteLine($"[collection] added {string.Join(", ", tags)}");

    [VeloxCommand(canValidate: true)]
    private void Promote() => Priority++;

    private partial bool CanExecutePromoteCommand(object? parameter) => Priority < 3;
}
```

命令签名画廊的共用来源：`Examples/MVVM/Common/Lib/CommandGalleryViewModel.cs`；属性与集合同一套模式见 `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`。

## 7. 运行声明

- ⚠️ 未实际运行——仅于 2026-11-25 静态核验。已对照生成器源码（`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs`、`Command.cs`、`Base/Analizer.cs`）、特性声明（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`、`VeloxCommandAttribute.cs`）以及两个 MVVM demo 核验。I/O 方案完整；本环境未执行 NuGet 还原与运行。
