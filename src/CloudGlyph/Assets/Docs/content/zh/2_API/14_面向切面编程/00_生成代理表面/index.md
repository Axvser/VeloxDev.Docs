# 生成代理表面

特性、标记接口、代理缓存以及生成器产出的成员。这里的运行时类型都在 `#if NET` 下编译。

## VeloxDev.AspectOriented

### 类：AspectOrientedAttribute

标记要织入的成员。

**签名：** `public class AspectOrientedAttribute : Attribute`

**特性用法：** `AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field`，`AllowMultiple = false`，`Inherited = false`。

公开属性或方法只需此特性。字段还需属性生成特性（`[VeloxProperty]`），生成的属性成为被拦截成员。

### 接口：IAspectOriented

生成器可织入类型的标记。生成的镜像接口实现它；原类不实现。

**签名：** `public interface IAspectOriented`

### 类：AopCache

每个 `(TClass, TInterface)` 组合一个弱代理缓存，由 CLR 泛型特化提供，而非逐类生成代码。

**签名：** `public static class AopCache`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Resolve<TClass, TInterface>` | `static TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory) where TInterface : class, IAspectOriented where TClass : class` | 返回 `instance` 的缓存代理，首次使用由 `factory` 创建。 |

`TInterface` 上的 `DynamicallyAccessedMembers(PublicParameterlessConstructor)` 标注仅为满足 `ConditionalWeakTable` 的裁剪器要求；该方法从不调用 `GetOrCreateValue`。

### 类：Aop

代理到目标的反向映射。

**签名：** `public static class Aop`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Map` | `static void Map(object proxy, object target)` | 登记代理到目标的映射。由生成的 `Aop()` 扩展调用。 |
| `GetTarget<TTarget>` | `static TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class` | 返回原对象，或 `null`。 |

## 生成的成员

对命名空间 `App.ViewModels` 下的分部类 `CounterViewModel`，生成器产出：

| 成员 | 名称 | 可见性 | 说明 |
|---|---|---|---|
| 镜像接口 | `VeloxDev.AopInterfaces` 中的 `CounterViewModel_App_ViewModels_Aop` | `public interface` | 实现 `IAspectOriented` 与 `IAopHookTarget`；镜像每个被织入成员。 |
| 代理 | `CounterViewModel_App_ViewModels_AopProxy` | `internal sealed class` | 实现镜像接口。名称为 `{Interface}Proxy`；不直接使用。 |
| 扩展类 | `VeloxDev.AspectOriented` 中的 `CounterViewModel_App_ViewModels_AopExtensions` | `public static class` | 声明 `Aop()`。 |
| 扩展方法 | `public static {Interface} Aop(this {Class} instance)` | `public static` | 经 `AopCache.Resolve` 解析，首次构造代理并调用 `Aop.Map`。 |

命名空间段把 `.` 替换为 `_`；全局命名空间中的类使用 `Global`。生成文件为 `{Class}_{Namespace}_AOP.g.cs`、`{Class}_{Namespace}_AopExt.g.cs`、`{Interface}.g.cs` 与 `{Interface}Proxy.g.cs`。

**成员键。** 属性拆成 `get_{Name}` 与 `set_{Name}`；方法使用自身名称。代理的 `IAopHookTarget.SetHooks` 只接受这些键，未知键抛异常。

## 示例

```csharp
using System;
using VeloxDev.AspectOriented;

var counter = new CounterViewModel();
var proxy = counter.Aop();          // VeloxDev.AopInterfaces.CounterViewModel_Global_Aop

Console.WriteLine(proxy.Value);     // 经代理读取
proxy.Value = 7;                    // 经代理写入

CounterViewModel? original = Aop.GetTarget<CounterViewModel>(proxy);
Console.WriteLine(ReferenceEquals(counter, original));   // True
```

接口类型在构建时生成，因此可显式命名或保持 `var`。安装行为见[钩子与安装](../01_钩子与安装/index.md)。

## 说明

- 直接在 `counter` 上调用会绕过所有钩子；只有代理会运行它们。
- 代理按目标实例缓存。同一对象两次 `Aop()` 返回同一代理。
- 生成的代理是使用方程序集中的普通 C#。此前的运行期 `DispatchProxy` 实现需要 `Reflection.Emit` 与 `RequiresDynamicCode`；本设计两者皆无。
