# 面向切面编程

在不改成员函数体的前提下，为属性 getter、属性 setter 与方法挂上前置/替换/后置钩子。生成器发出镜像接口与代理；只有通过 `Aop()` 调用，钩子才会执行。

## 1. 前置条件

- **目标框架**：`VeloxDev.Core` 仅在定义了 `NET` 符号时构建 AOP 运行时，因此消费者必须面向 **.NET 5.0 或更高**（`netstandard2.0` 与 `netframework4.6.1` 不包含 `VeloxDev.AspectOriented`）。本示例使用 `net8.0`。
- **`VeloxDev.Core`** 与 **`VeloxDev.Core.Generator`**（分析器；NuGet 引用 Core 会带上它，`ProjectReference` 不会）。
- .NET SDK 8.0 或更高。无需服务，也不需要 GUI。

## 2. 安装/引入依赖

```text
dotnet new console -n AopQuickStart
cd AopQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 两个包还原成功；工程面向 `net8.0`；首次构建后生成器发出 `*_AOP.g.cs`、`*_AopExt.g.cs`、`<接口>.g.cs` 与 `<接口>Proxy.g.cs`。

## 3. 基础配置/注册

把类标成 `partial`，并在每个需要拦截的成员上写 `[AspectOriented]`。字段还需要属性生成特性（`[VeloxProperty]`）；普通属性可以单独使用。

```csharp
using VeloxDev.AspectOriented;

public partial class CounterViewModel
{
    [AspectOriented]
    public int Value { get; set; }

    [AspectOriented]
    public void Reset() => Value = 0;
}
```

**预期结果：** 借助 `using VeloxDev.AspectOriented;`，`counter.Aop()` 可解析并返回生成的接口。类本身不实现该接口，代理才实现。

## 4. 核心用法（逐步构建）

### 4.1 取得代理

`Aop()` 为每个目标缓存一个代理并返回它。返回的接口镜像所有 `[AspectOriented]` 成员，调用方可以像使用原对象一样使用它。底层的同一张缓存由 `AopCache.Resolve<TClass, TInterface>` 提供；反向查找是 `Aop.GetTarget<TTarget>(proxy)`。

```csharp
var counter = new CounterViewModel();
var proxy = counter.Aop();
```

**预期结果：** 对同一对象调用两次返回同一个代理。直接调用 `counter` 的成员仍然绕过所有钩子。

### 4.2 安装三个阶段

`SetProxy` 接收成员种类、成员的原始名，以及按 start / coverage / end 顺序排列的三个委托。阶段签名是 `ProxyHandler(object?[]? parameters, object? previous)`。

- `start` 在成员之前运行，返回值成为下一阶段的 `previous`。
- `coverage` 非空时替换成员：函数体不运行，它的返回值就是成员结果。
- `end` 在成员之后运行，返回值被丢弃。

getter 的 `parameters` 为 `null`；setter 的单个元素是被写入的值；方法的则是它自己的实参。

```csharp
proxy.SetProxy(ProxyMembers.Setter, nameof(CounterViewModel.Value),
    null,
    null,
    (parameters, previous) => { Console.WriteLine($"[setter after] {parameters?[0]}"); return null; });
```

**预期结果：** 执行 `proxy.Value = 7` 时先运行真实 setter，随后打印 `[setter after] 7`。

### 4.3 通过代理读写与调用

```csharp
Console.WriteLine(proxy.Value);
proxy.Value = 7;
proxy.Reset();
```

**预期结果：** getter 钩子在真实 getter 之前；setter 钩子在写入之后；`Reset` 与其他方法一样会被拦截。

### 4.4 替换成员

在 `Reset` 上安装 `coverage` 后，它的函数体不再运行。处理器的返回值就是方法结果（`void` 方法会忽略它）。

```csharp
proxy.SetProxy(ProxyMembers.Method, nameof(CounterViewModel.Reset),
    null,
    (parameters, previous) => { Console.WriteLine("[reset replaced]"); return null; },
    null);
```

**预期结果：** `proxy.Reset()` 打印 `[reset replaced]`，并让 `Value` 保持为 7。

### 4.5 组合与替换语义

对同一成员再次安装会**替换**全部三个阶段，不会叠加；也无法保留其中一个阶段、只替换另一个。要移除某成员的钩子，安装一个三个阶段全为 `null` 的集合。支持 `[VeloxProperty][AspectOriented]` 字段：生成的属性成为被拦截成员，名字的推导与 MVVM 生成器完全一致（`_name` 变成 `Name`）。重载方法无法挂钩——拦截键就是不带签名的方法名。

`SetProxy` 会拒绝不是代理的对象，而不是静默安装永远不执行的钩子。

**预期结果：** 对 `Value`/`Getter` 第二次调用 `SetProxy` 会替换第一个处理器；在 `counter`（而非 `proxy`）上安装会抛 `InvalidOperationException`。

## 5. 验证

运行完整程序。输出顺序即可证明各阶段：

```text
[getter before]
read: 0
[setter after] 7
[reset replaced]
[getter before]
read after replaced Reset: 7
```

最后一次读取是 7 而不是 0：被替换的 `Reset` 从未执行函数体。

## 6. 完整代码

```csharp
using System;
using VeloxDev.AspectOriented;

var counter = new CounterViewModel();
var proxy = counter.Aop();

proxy.SetProxy(ProxyMembers.Getter, nameof(CounterViewModel.Value),
    (parameters, previous) => { Console.WriteLine("[getter before]"); return null; },
    null,
    null);

proxy.SetProxy(ProxyMembers.Setter, nameof(CounterViewModel.Value),
    null,
    null,
    (parameters, previous) => { Console.WriteLine($"[setter after] {parameters?[0]}"); return null; });

proxy.SetProxy(ProxyMembers.Method, nameof(CounterViewModel.Reset),
    null,
    (parameters, previous) => { Console.WriteLine("[reset replaced]"); return null; },
    null);

Console.WriteLine($"read: {proxy.Value}");
proxy.Value = 7;
proxy.Reset();
Console.WriteLine($"read after replaced Reset: {proxy.Value}");

public partial class CounterViewModel
{
    [AspectOriented]
    public int Value { get; set; }

    [AspectOriented]
    public void Reset() => Value = 0;
}
```

Demo 证据：`Examples/AOP/WPF/Demo/MainWindow.xaml.cs` 安装同样的三个阶段；`Examples/AOP/WPF/Demo/TeamViewModel.cs` 展示了字段上的 `[VeloxProperty][AspectOriented]`。

## 7. 运行声明

- ⚠️ 未实际运行——仅于 2026-11-25 静态核验。已对照 `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`、`AspectHooks.cs`、`Aop.cs`、`AspectOrientedAttribute.cs`、`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`、`Writers/AopWriter.cs` 以及 WPF/Avalonia 的 AOP demo 核验。本环境未执行构建。
