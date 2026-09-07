# MVVM — 定义可观察属性

`[VeloxProperty]` 是标记特性（`AttributeTargets.Field | AttributeTargets.Property`），没有参数。生成器把被标记的成员改写为公开可观察属性加 `partial` 钩子声明，并且只合成类层级里尚不存在的通知基础设施。

## 1. 字段写法（每个支持目标都可用）

标记私有字段即可；属性名由字段名首字母大写派生（`_count` → `Count`、`_greeting` → `Greeting`）：

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private int _count;
}
```

生成器（`MVVMWriter`）把属性与钩子声明写入同一类的另一个 partial 部分。对于上述字段，生成的 setter 体是：

```csharp
public int Count
{
    get => _count;
    set
    {
        if (global::System.Object.Equals(_count, value)) return;
        var old = _count;
        OnPropertyChanging(nameof(Count));
        OnCountChanging(old, value);
        _count = value;
        OnCountChanged(old, value);
        OnPropertyChanged(nameof(Count));
    }
}

partial void OnCountChanging(int oldValue, int newValue);
partial void OnCountChanged(int oldValue, int newValue);
```

然后你在自己的文件里用相同签名的 `partial` 方法实现钩子：

```csharp
public partial class CounterViewModel
{
    partial void OnCountChanged(int oldValue, int newValue)
    {
        System.Console.WriteLine($"[hook] Count {oldValue} -> {newValue}");
    }
}
```

**预期结果：** `_count` 以 `public int Count` 暴露；执行 `Count = 5` 依次 (1) 调 `OnPropertyChanging(nameof(Count))` → 触发 `PropertyChanging`，(2) `partial OnCountChanging(old, new)`，(3) 字段赋值，(4) `partial OnCountChanged(old, new)` → 打印 `[hook] Count 0 -> 5`，(5) `OnPropertyChanged(nameof(Count))` → 触发 `PropertyChanged`。再次赋相同的值会在 `Object.Equals` 守卫处短路 —— 没有事件、没有钩子调用。

## 2. partial 属性写法（C# 13）

用 C# 13 partial 属性代替字段。生成器补上实现访问器与名为 `_<名称>` 的后备字段：

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] public partial string Greeting { get; set; }
}
```

这是真实用法 —— `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpServerConfiguration.cs` 用这种方式标注了它所有配置成员，没有基类、没有任何样板代码。

**预期结果：** 生成同样的公开属性、后备字段与 `OnGreetingChanging` / `OnGreetingChanged` 钩子；类无需手动实现 `INotifyPropertyChanged`。

## 3. 通知基础设施按类自动探测

`MVVMWriter` 在生成前检查整个层级：

- **基类未提供** → 生成器给类加上 `INotifyPropertyChanging` / `INotifyPropertyChanged`，并发出 `public event PropertyChangingEventHandler? PropertyChanging;`、`public event PropertyChangedEventHandler? PropertyChanged;`、`public virtual void OnPropertyChanging(string propertyName)`、`public virtual void OnPropertyChanged(string propertyName)`（事件由这两个方法触发）。
- **基类已提供事件/方法**（例如演示自带、实现接口并声明 `OnPropertyChanging(string)` / `OnPropertyChanged(string)` 的 `ObservableViewModelBase`）→ 生成器复用它们，**不再重复生成**。
- **探测到知名的 MVVM 基类** → 生成的 setter 委托给该框架自己的通知器而不是直接拨动事件：CommunityToolkit.Mvvm 的 `ObservableObject`/`[ObservableObject]` 与 Prism 的 `BindableBase` → `SetProperty(...)`，ReactiveUI 的 `ReactiveObject` → `RaiseAndSetIfChanged(...)`，Caliburn.Micro 的 `PropertyChangedBase` → `NotifyOfPropertyChange(...)`。这让 VeloxDev 属性能够活在你已经在用的 MVVM 视图模型基类里。

**预期结果：** 裸 `partial class` 编译成满足 `INotifyPropertyChanging` 与 `INotifyPropertyChanged` 的类型；继承自已实现它们的基类的类只新增被标注的属性与钩子 —— 两种情况订阅事件的观察行为一致。

## 4. 生成代码的去向

每个被标注的类一个 `.g.cs` 文件，命名为 `{类名}_{下划线命名空间}_MVVM.g.cs`，例如 `CounterViewModel_QuickStart_Mvvm_MVVM.g.cs`（`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs` 里的方法 `GetFileName()`）。同一命名空间里两个类产生两个文件 —— 按类逐个生成。

**预期结果：** 构建后文件出现在 `obj/<配置>/<目标框架>/generated/` 下；在 IDE 里双击可看到上述属性、钩子以及（仅在需要时）通知成员。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。生成的形态转录自 `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs`（`MVVMPropertyFactory.GenerateViewModel`、setter 体构造器）与 `MVVMWriter.cs`；partial 属性示例取自 `McpServerConfiguration.cs` 的真实代码。
