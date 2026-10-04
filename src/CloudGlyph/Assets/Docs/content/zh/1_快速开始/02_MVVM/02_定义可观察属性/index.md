# MVVM — 定义可观察属性

`[VeloxProperty]` 是一个无参数的标记特性（`AttributeTargets.Field | AttributeTargets.Property`）。生成器把被标注的成员改写成公开可观察属性并声明 `partial` 钩子，且只补齐该类层级中尚不存在的通知基础设施。

## 1. 字段写法（在所有支持目标上可用）

标注一个私有字段；属性名由字段名去掉前导 `_` 并把下一个字符大写得到（`_count` → `Count`）：

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private int _count;
}
```

下面这段就是**该成员真实生成的代码**（产出方式见运行声明）：

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if (global::System.Object.Equals(this._count, value)) return;
        var old = this._count;
        OnPropertyChanging(nameof(Count));
        OnCountChanging(old, value);
        this._count = value;
        OnCountChanged(old, value);
        OnPropertyChanged(nameof(Count));
    }
}
partial void OnCountChanging(System.Int32 oldValue, System.Int32 newValue);
partial void OnCountChanged(System.Int32 oldValue, System.Int32 newValue);
```

钩子由你在类的另一半实现；声明由生成器产出，所以签名写错是编译错误，而不是一个被悄悄忽略的方法：

```csharp
public partial class CounterViewModel
{
    partial void OnCountChanged(int oldValue, int newValue)
    {
        System.Console.WriteLine($"[count] {oldValue} -> {newValue}");
    }
}
```

**预期结果：** `_count` 以 `public int Count` 暴露。执行 `Count = 3` 会按顺序触发：(1) `OnPropertyChanging(nameof(Count))` → 触发 `PropertyChanging`；(2) `partial OnCountChanging(old, new)` 钩子；(3) 字段赋值；(4) `partial OnCountChanged(old, new)` 钩子 → 打印 `[count] 0 -> 3`；(5) `OnPropertyChanged(nameof(Count))` → 触发 `PropertyChanged`。再次赋相同值会在 `Object.Equals` 守卫处短路：无事件、无钩子。

## 2. partial 属性写法（C# 13）

改用 C# 13 的 partial 属性声明。生成器补齐实现访问器以及一个后备字段：

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] public partial string Greeting { get; set; }
}
```

仓库中就有真实用法 —— `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpServerConfiguration.cs` 用这种方式标注了它的全部配置成员，既无基类也无样板代码。

**预期结果：** 会生成同样的公开属性与 `OnGreetingChanging` / `OnGreetingChanged` 钩子；该类依然不需要手写 `INotifyPropertyChanged` 实现。

## 3. 通知基础设施按类检测

MVVM writer 在生成前会遍历该类及其基类，只补缺失的部分（上面那份生成文件就展示了裸 `partial class` 的情况）：

- **基类没有提供** → 生成器把 `INotifyPropertyChanging` / `INotifyPropertyChanged` 加到该 partial 类上，并生成 `public event PropertyChangingEventHandler? PropertyChanging;`、`public event PropertyChangedEventHandler? PropertyChanged;`、`public virtual void OnPropertyChanging(string propertyName)` 与 `public virtual void OnPropertyChanged(string propertyName)`。
- **基类已经提供事件与方法**（例如演示自带的 `ObservableViewModelBase`）→ 生成器复用之，不产生重复成员。
- **识别出已知 MVVM 基类**（CommunityToolkit.Mvvm、Prism、ReactiveUI、Caliburn.Micro）→ 生成的 setter 改为委托给该框架自己的通知方法（`SetProperty`、`RaiseAndSetIfChanged`、`NotifyOfPropertyChange`），而不是直接触发本地事件。

**预期结果：** 裸 `partial class` 编译出的类型同时满足两个通知接口；从已实现它们的基类派生的类只多出被标注的属性与钩子。两种情况下订阅事件的行为完全一致。

## 4. 生成代码落在哪里

每个被标注的类一个文件，文件名来自 `Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs` 的 `GetFileName()`，形如 `{类名}_{命名空间下划线化}_MVVM.g.cs`。生成是**按类**进行的：同一命名空间里的两个类产生两个文件。

**预期结果：** 用 `-p:EmitCompilerGeneratedFiles=true` 构建后，文件出现在 `obj/<配置>/<目标框架>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/` 下。不加该开关时代码仍会被编译进去，只是只能通过 IDE 的生成文件节点查看。

## 运行声明

- ✅ 2026-10-01 实际构建并运行过。在一个临时目录的控制台项目中引用了 `VeloxDev.Core.csproj`，并以 analyzer 方式（Debug）引用 `VeloxDev.Core.Generator.csproj`，声明了 `[VeloxProperty] private int _count;`、`[VeloxProperty] private ObservableCollection<string> _items = [];` 以及一个负责打印的 `partial void OnCountChanged` 钩子，用 `dotnet run -c Debug` 运行。录制输出（前三行来自本页的成员）：

  ```text
  [collection] added: ready
  initial: Count=0, CanExecute(Decrement)=False
  Items: ready
  [count] 0 -> 3
  ```

- 第 1、3 节引用的生成代码逐字抄自同一次构建产出的 `obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/CounterViewModel_QuickStart_Mvvm_MVVM.g.cs`，并非手工还原。第 2 节的 `partial` 属性写法本次**没有**编译（需要 C# 13 语言级别），其结论来源于 `McpServerConfiguration.cs`。
