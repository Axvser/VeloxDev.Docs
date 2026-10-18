# AOP — 生成器产物

`Src/Generators/VeloxDev.Core.Generator` 中的两个增量生成器产出调用方触达的全部内容：

| 生成器 | 源码 | 发射 |
|---|---|---|
| `VeloxDev.Generators.AopSurface` | `AopSurface.cs` | 镜像接口与代理类（两个文件） |
| `VeloxDev.Generators.AopProxy` | `AopProxy.cs` → `Writers/AopWriter.cs` | `Aop()` 扩展 |

用户类不会被注入任何东西。`AopWriter.GenerateBaseTypes` 与 `GenerateBaseInterfaces` 返回空数组，`GenerateBody` 返回空字符串 —— 旧的 partial 类胶水已不存在。

## 发现

`Analizer.Filters.Targets` 使用 `ForAttributeWithMetadataName("VeloxDev.AspectOriented.AspectOrientedAttribute", ...)`，`IsCandidateClass` 只接受 **partial** 类声明。随后 `AnalizeHelper.IsAopClass` 跨所有 partial 声明按特性简单名复查成员。由此可知：

- 类必须是 `partial`；
- 写 `[AspectOriented]`，不要写限定名或别名形式；
- 跨多个 partial 文件的类型只生成一次，成员从所有部分收集。

## 命名

`Base/AopNames.cs` 是唯一的命名算法：

```csharp
internal const string InterfaceNamespace = "VeloxDev.AopInterfaces";

internal static string InterfaceFor(INamedTypeSymbol symbol)
    => $"{symbol.Name}_{Segment(symbol)}_Aop";

internal static string ProxyFor(INamedTypeSymbol symbol)
    => InterfaceFor(symbol) + "Proxy";

internal static string Segment(INamedTypeSymbol symbol)
    => symbol.ContainingNamespace is null || symbol.ContainingNamespace.IsGlobalNamespace
        ? "Global"
        : symbol.ContainingNamespace.ToDisplayString().Replace('.', '_');
```

示例：`Demo.TeamViewModel` → `TeamViewModel_Demo_Aop`；`Demo.ViewModels.TeamViewModel` → `TeamViewModel_Demo_ViewModels_Aop`；全局命名空间的类 → `{Class}_Global_Aop`。

## 生成的接口

文件名提示 `{Interface}.g.cs`，命名空间 `VeloxDev.AopInterfaces`。以 `AopFixture`（命名空间 `VeloxDev.Core.Test.AspectOriented`）为例，发射的声明是：

```csharp
public interface AopFixture_VeloxDev_Core_Test_AspectOriented_Aop : global::VeloxDev.AspectOriented.IAspectOriented, global::VeloxDev.AspectOriented.IAopHookTarget
{
    public string Title { get; set; }

    public int Add(int a, int b);
    public void Ping();
    public string Echo(string value);
}
```

成员规则出自 `AopSurface.GenerateSource`：

| 源成员 | 条件 | 接口成员 |
|---|---|---|
| 字段 | `[AspectOriented]` 外加文本含 `Observable` 或 `Property` 的特性 | `get`/`set` 属性；名称为去掉前导 `_` 并把下一字符大写（`_name` → `Name`） |
| 属性 | `public` 且带 `[AspectOriented]`；存在公有 getter 或未声明 getter 时镜像 getter；仅当存在公有 setter 时镜像 setter | 同名属性 |
| 方法 | `public` 且带 `[AspectOriented]` | 同名方法，参数与返回类型为全限定名 |

属性的 getter 与 setter 是独立成员，拥有独立的钩子组。

## 生成的代理

文件名提示 `{Interface}Proxy.g.cs`，命名空间 `VeloxDev.AopInterfaces`：

```csharp
internal sealed class AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy : AopFixture_VeloxDev_Core_Test_AspectOriented_Aop
{
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Add;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Ping;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Echo;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_get_Title;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_set_Title;

    private readonly global::VeloxDev.Core.Test.AspectOriented.AopFixture _target;

    internal AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(global::VeloxDev.Core.Test.AspectOriented.AopFixture target) => _target = target;
    // 成员与 SetHooks ...
}
```

它是 `internal sealed`；调用方只看到 `Aop()` 返回的接口类型。其行为与异常面见 [生成的代理](../00_面向切面/03_生成的代理/index.md)。

## 生成的扩展

文件名提示 `{Class}_{NamespaceSegment}_AopExt.g.cs`，命名空间 `VeloxDev.AspectOriented`，类名 `{Class}_{NamespaceSegment}_AopExtensions`。`AopFixture` 的实际发射输出：

```csharp
namespace VeloxDev.AspectOriented;

public static class AopFixture_VeloxDev_Core_Test_AspectOriented_AopExtensions
{
    public static global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_Aop Aop(this global::VeloxDev.Core.Test.AspectOriented.AopFixture instance)
        => global::VeloxDev.AspectOriented.AopCache.Resolve<
            global::VeloxDev.Core.Test.AspectOriented.AopFixture,
            global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_Aop>(
            instance,
            static x =>
            {
                var p = new global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(x);
                global::VeloxDev.AspectOriented.Aop.Map(p, x);
                return p;
            });
}
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `instance` | 模型类 | 目标实例 |

**返回：** 生成的接口 —— 经 `AopCache.Resolve` 每个实例一个缓存代理。

**生成文件路径：** 默认 Roslyn 只把这些源交给编译器。设置 `EmitCompilerGeneratedFiles=true` 后可在 `obj/<Configuration>/<TFM>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.{AopSurface,AopProxy}/` 下查看。上面的片段来自 `Src/Core/VeloxDev.Core.Test` 的发射文件（`obj/Debug/net10.0/generated/...`）。

## 限制（源码核验）

| 形态 | 结果 | 原因 |
|---|---|---|
| 非 partial 类 | 不生成任何内容，无诊断 | `IsCandidateClass` 要求 `partial` |
| 重载方法 | 生成代码无法编译 | 每个裸名只有一个钩子字段与一个 `switch` 分支 |
| 泛型方法 | 生成接口丢失类型参数列表 | `MethodDeclaration(...)` 创建时未调用 `WithTypeParameterList` |
| `ref` / `out` / `in` 参数 | 生成的调用丢失修饰符 | 代理以裸标识符调用 `_target.M(arg1, ...)` |
| 非公有方法或非公有访问器 | 不镜像 | `AopSurface` 中的 `public` 过滤 |

被拦截成员应保持为实例成员、名称唯一、参数均为按值传递。
