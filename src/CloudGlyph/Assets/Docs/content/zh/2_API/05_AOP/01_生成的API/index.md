# AOP — 生成器产物（源生成器）

对每个至少有一个成员带 `[AspectOriented]` 的 `partial` 类在编译期生成（识别逻辑在 `Base/AnalizeHelper.IsAopClass` 与 `Writers/AopWriter.ReadAopConfig`）。共三种产物，来自 `Src/Generators/VeloxDev.Core.Generator` 的生成器：

| 产物 | 生成者 | 文件名提示 |
|---|---|---|
| AOP 代理接口 | `AopInterface` | `{Class}_{Ns}_Aop.g.cs` |
| partial 类胶水 | `AopProxy` → `AopWriter.Write` | `{Class}_{Ns}_AOP.g.cs` |
| `Aop(this T)` 扩展 | `AopProxy` → `AopWriter.WriteExtension` | `{Class}_{Ns}_AopExt.g.cs` |

`Ns` 是类所在命名空间把 `.` 替换为 `_` 之后的结果（对文件级命名空间的 `Demo.TeamViewModel`，`Ns = Demo`）。

## 生成类型：`VeloxDev.AopInterfaces.{Class}_{Ns}_Aop`

命名规则出自 `AopInterface.cs`：

```csharp
string interfaceName = $"{classDeclaration.Identifier.Text}_{classSymbol.ContainingNamespace.ToDisplayString().Replace('.', '_')}_Aop";
```

`public`，继承 `global::VeloxDev.AspectOriented.IAspectOriented`。示例：`Demo.TeamViewModel` → `TeamViewModel_Demo_Aop`；`Demo.ViewModels.TeamViewModel` → `TeamViewModel_Demo_ViewModels_Aop`。

**生成的成员**（为类的每个合格成员生成一个公有成员，按成员类别依次排列）：

- **字段**：同时带有 `[AspectOriented]` 与简单名含 `Observable` 或 `Property` 的特性（例如 `[VeloxProperty]`、`[Observable]`）时，成为一个 get/set 属性。名称去掉前导 `_` 并把下一字符大写（`Base/AnalizeHelper.GetPropertyNameByFieldName`）：`_name` → `Name`。
- **公有属性**：带 `[AspectOriented]` 时成为一个属性 —— 当不存在 getter 或 getter 为公有时保留 getter；仅当存在公有 setter 时保留 setter。
- **公有方法**：带 `[AspectOriented]` 时成为一个方法；参数与返回类型改写为语义模型解析出的全限定显示形式（`void` 保持 `void`）。

`AopInterface` 对 WPF demo 类 `Demo.TeamViewModel` 生成的接口的可读渲染（实际生成器写的是语义模型解析出的全限定类型名）：

```csharp
public interface TeamViewModel_Demo_Aop : global::VeloxDev.AspectOriented.IAspectOriented
{
    string Name { get; set; }
    ObservableCollection<MemberViewModel> Members { get; set; }
    void Reset();
    void AOP_OnMemberAdded(object? sender, NotifyCollectionChangedEventArgs e);
    void AOP_OnMemberRemoved(object? sender, NotifyCollectionChangedEventArgs e);
}
```

`Name` / `Members` 来自 `TeamViewModel.cs` 的两个 `[VeloxProperty][AspectOriented]` 字段；`Reset`、`AOP_OnMemberAdded`、`AOP_OnMemberRemoved` 来自 `[AspectOriented]` 公有方法。该类型被传给 `DispatchProxy.Create<T, ProxyInstance>()`，这正是运行时能拦截 `get_*` / `set_*` / 方法名的原因（`AspectOrientedAttribute` 见 [特性与标记](../00_面向切面/00_特性与标记/index.md)）。

## 生成的 partial 类（文件 `{Class}_{Ns}_AOP.g.cs`）

`AopProxy`（命名空间 `VeloxDev.Generators`）收集每个通过过滤的类，当 `AopWriter.CanWrite()` 为真（存在 `[AspectOriented]` 成员）时，经继承的 `WriterBase.Write()` 产出一个源文件：重发所属命名空间，并把类重新声明为 `partial`，其基类型列表 = 符号原有的基类型 + 生成的 AOP 接口（`AopWriter.GenerateBaseInterfaces`），方法体为空。

真实契约出自 `Writers/AopWriter.cs`：

```csharp
public override string[] GenerateBaseInterfaces() =>
[
    $"{NAMESPACE_VELOX_AOP}.{Syntax?.Identifier.Text}_{Symbol?.ContainingNamespace.ToDisplayString().Replace('.', '_')}_Aop"
];
```

其中 `NAMESPACE_VELOX_AOP = "global::VeloxDev.AopInterfaces"`（`Writers/WriterBase.cs`）。效果：编译器因此看到该类实现了它的生成接口，从而由用户自己 `partial` 部分提供的成员满足接口契约 —— 模型源码无需自行声明该接口。

## 生成的扩展：`{Class}_{Ns}_AopExtensions` 中的 `Aop(this T)`

`AopWriter.WriteExtension()` 在命名空间 `VeloxDev.AspectOriented` 下发射文件 `{Class}_{Ns}_AopExt.g.cs`。对 WPF demo 的 `Demo.TeamViewModel` 的具体输出：

```csharp
namespace VeloxDev.AspectOriented;

public static class TeamViewModel_Demo_AopExtensions
{
    public static global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop Aop(
        this global::Demo.TeamViewModel instance)
        => global::VeloxDev.AspectOriented.AopCache.Resolve<
            global::Demo.TeamViewModel,
            global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop>(
            instance,
            static x =>
            {
                var p = global::VeloxDev.AspectOriented.ProxyEx.CreateProxy<global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop>(x);
                global::VeloxDev.AspectOriented.Aop.Map(p, x);
                return p;
            });
}
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `instance` | `T`（模型类） | 要包装的目标实例 |

**返回：** `{Class}_{Ns}_Aop` — 缓存的代理（每个实例一个，经 `AopCache.Resolve`），类型为生成的接口。

**备注：**

- 通过 `AopCache.Resolve<TClass, TInterface>` 解析（见 [Aop 与 AopCache](../00_面向切面/04_代理生命周期/index.md)）；其执行的工厂调用 `ProxyEx.CreateProxy<I>(x)` 与 `Aop.Map(p, x)`。
- Demo 用法，`Examples/AOP/WPF/Demo/MainWindow.xaml.cs`：

```csharp
var team = _teamData.Aop();     // 缓存的代理
_ = _teamData.Aop().Name;       // getter 被拦截（start 钩子触发）
_teamData.Aop().Reset();        // 方法被拦截（coverage 替换成员体）
```

相关页面：[AOP 运行时概览](../00_面向切面/index.md)。
