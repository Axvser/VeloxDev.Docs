# AOP 运行时 — 命名空间 `VeloxDev.AspectOriented`（`#if NET`）

本节列出的每个文件都在 `#if NET` 内，因此这些类型只存在于 `VeloxDev.Core` 的 `net5.0` 与 `net8.0` 资产中，不存在于 `netstandard2.0`、`netframework4.6.1` 或 `netcoreapp3.0`。

运行时之所以很小，是因为拦截本身是生成代码，而不是运行期工厂。生成的代理类实现生成的接口，每个成员要么直接调用目标（无钩子），要么运行钩子管线。运行时类型只提供契约（`AspectHooks`、`ProxyHandler`、`IAopHookTarget`）、注册辅助（`ProxyEx`）与生命周期映射（`Aop`、`AopCache`）。

## 子页面

| 页面 | 内容 |
|---|---|
| [AspectOrientedAttribute 与 IAspectOriented](00_特性与标记/index.md) | 声明面与标记契约 |
| [ProxyMembers、ProxyHandler、AspectHooks、IAopHookTarget](01_代理成员处理器/index.md) | 钩子契约与拦截键 |
| [ProxyEx](02_代理扩展/index.md) | `SetProxy` —— 唯一的公开注册方法 |
| [生成的代理](03_生成的代理/index.md) | 每次调用时发射类的行为，以及可能抛出的异常 |
| [Aop 与 AopCache](04_代理生命周期/index.md) | 反向映射与按实例缓存 |

面向用户的入口 `Aop(this T)` 是生成产物，不属于本命名空间；参见 [生成器产物](../01_生成的API/index.md)。
