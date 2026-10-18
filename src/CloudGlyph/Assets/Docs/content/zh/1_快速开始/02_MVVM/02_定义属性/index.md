# MVVM — 定义可观察属性

`[VeloxProperty]`（`AttributeTargets.Field | AttributeTargets.Property`，无参数，非 sealed）标记一个成员，由 `VeloxDev.Generators.MVVM` 改写为可观察属性。

## 1. 字段形态

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private int _count;
}
```

属性名会去掉开头的 `_` 并把下一个字符大写（`_count` → `Count`）。生成的属性是：

```csharp
public System.Int32 Count
{
    get => this._count;
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
}
partial void OnCountChanging(System.Int32 oldValue, System.Int32 newValue);
partial void OnCountChanged(System.Int32 oldValue, System.Int32 newValue);
```

在同一个类的另一部分实现这些钩子。由于声明由生成器给出，签名不一致会变成编译错误，而不是被静默忽略。

```csharp
public partial class CounterViewModel
{
    partial void OnCountChanged(int oldValue, int newValue)
    {
        System.Console.WriteLine($"[count] {oldValue} -> {newValue}");
    }
}
```

**预期结果：** `Count = 3` 依次触发 `PropertyChanging`、`OnCountChanging`、字段赋值、`OnCountChanged`（打印 `[count] 0 -> 3`）、`PropertyChanged`。再次赋同一个值会在相等性守卫处提前返回：不发事件、不调钩子。

## 2. partial 属性形态（C# 13）

```csharp
[VeloxProperty] public partial string Greeting { get; set; }
```

生成器补全访问器，并生成名为 `_greeting` 的 backing field，同时保留你声明的可访问性与访问器可见性。非 `partial` 的属性无法补全；生成器会报告 `VELOX_MVVM_PROP003` 并跳过它。

**预期结果：** 同样生成 `Greeting` 属性以及 `OnGreetingChanging` / `OnGreetingChanged` 钩子。

## 3. 按类探测通知基础设施

生成前，写入器会检查该类及其基类：

- **完全没有** → 类型获得 `INotifyPropertyChanging` / `INotifyPropertyChanged`、`PropertyChanging` / `PropertyChanged` 事件，以及 `OnPropertyChanging(string)` / `OnPropertyChanged(string)`。
- **基类已经提供**（例如示例中的 `ObservableViewModelBase`）→ 不重复生成，生成的 setter 调用继承来的方法。
- **识别到已知框架基类** → 生成的 setter 委托给该框架的通知器：CommunityToolkit.Mvvm 与 Prism（`SetProperty(ref T, T, string)`）、ReactiveUI（`RaiseAndSetIfChanged`）、Caliburn.Micro（`NotifyOfPropertyChange`）。

**预期结果：** 裸 `partial class` 编译出的类型实现两个通知接口；已经具备这些接口的基类派生类只多出被标注的属性与钩子。订阅事件的行为在两种情况下一致。

## 4. 诊断与生成文件

| 诊断 | 级别 | 条件 |
| --- | --- | --- |
| `VELOX_MVVM_PROP001` | Error | 两个成员映射到同一个属性名，或已有字段无法支撑该属性（const/static/readonly，或类型不同） |
| `VELOX_MVVM_PROP002` | Warning | 字段名推不出合法标识符 |
| `VELOX_MVVM_PROP003` | Warning | 被标注的属性不是 `partial`，访问器无法补全 |

每个类一个文件：`{类名}_{命名空间下划线化}_MVVM.g.cs`。构建时传入 `-p:EmitCompilerGeneratedFiles=true`，它会出现于 `obj/<Configuration>/<TargetFramework>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/`。

**预期结果：** 错误声明会在作者自己的代码行上报告诊断 id；正确声明每个类产出一个生成文件。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 仅对照 `Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs`、`Base/Analizer.cs`（`MVVMPropertyFactory`）与 `Diagnostics.cs` 做了静态核对。生成的 setter 与钩子声明转写自这些模板；`partial` 属性形态来自写入器源码，未在此编译。
