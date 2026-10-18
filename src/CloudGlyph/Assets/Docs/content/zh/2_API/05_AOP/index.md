# AOP — API 参考

面向 `.NET 5+` 目标的切面拦截。`AspectOrientedAttribute` 标记 `partial` 类的成员；源生成器产出镜像接口、密封代理类与带缓存的 `Aop()` 扩展方法。运行时通过 `ProxyEx.SetProxy` 按成员安装钩子，并按 `start` / `coverage` / `end` 三段执行。

## 公开面

**运行时 —— 命名空间 `VeloxDev.AspectOriented`（`#if NET`）**

| 类型 | 类别 | 作用 |
|---|---|---|
| `AspectOrientedAttribute` | 特性 | 标记要镜像的成员 |
| `IAspectOriented` | 接口 | 空标记，所有生成接口都实现它 |
| `ProxyMembers` | 枚举 | `Getter`、`Setter`、`Method` —— 选择访问器与键 |
| `ProxyHandler` | 委托 | `object? (object?[]? parameters, object? previous)` |
| `AspectHooks` | 密封类 | 一组 `(start, coverage, end)` |
| `IAopHookTarget` | 接口 | `SetHooks(string memberKey, AspectHooks? hooks)` —— 由生成的代理实现 |
| `ProxyEx` | 静态类 | `SetProxy` —— 安装一组钩子 |
| `Aop` | 静态类 | `Map` / `GetTarget` —— 代理到目标的反向映射 |
| `AopCache` | 静态类 | `Resolve` —— 每个目标实例一个代理 |

**生成产物 —— 命名空间 `VeloxDev.AopInterfaces`，外加 `VeloxDev.AspectOriented` 中的扩展**

| 产物 | 名称 |
|---|---|
| 接口 | `{Class}_{NamespaceSegment}_Aop : IAspectOriented, IAopHookTarget` |
| 代理 | `internal sealed class {Interface}Proxy : {Interface}` |
| 扩展 | `{Class}_{NamespaceSegment}_AopExtensions.Aop(this Class)` |

## 章节

- [AOP 运行时 —— 命名空间 `VeloxDev.AspectOriented`](00_面向切面/index.md) —— 标记特性、钩子契约、注册、生成的代理与生命周期缓存。
- [生成器产物](01_生成的API/index.md) —— 命名、成员规则、发射产物与限制。

## 证据来源

- **测试：** `Src/Core/VeloxDev.Core.Test/AspectOriented/` —— `AopFixture.cs`、`AopProxyTests.cs`（13 个测试，全部通过）。
- **Demo：** `Examples/AOP/WPF/Demo`、`Examples/AOP/Avalonia/Demo`。
- **运行时：** `Src/Core/VeloxDev.Core/AspectOriented/*.cs`、`Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`。
- **生成器：** `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`、`AopProxy.cs`、`Base/AopNames.cs`、`Writers/AopWriter.cs`。

以下成员均已对照上述文件核验；测试钉住了阶段顺序、替换语义、缓存、错误行为与可回收性。
