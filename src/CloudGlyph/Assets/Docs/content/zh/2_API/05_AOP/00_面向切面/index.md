# AOP 运行时 — 命名空间 `VeloxDev.AspectOriented`（`#if NET`）

每个运行时源文件都在 `#if NET` 条件下编译，因此下述类型只存在于 `VeloxDev.Core` 的 `net5.0` 目标 —— 它是该项目唯一的 `NET` 目标。引用该资产的 .NET 5.0 及以上工程即可使用本功能；两个 Demo 均基于它构建（Avalonia Demo 为 `net9.0`，WPF Demo 为 `net9.0-windows`）。

运行时构建在 `System.Reflection.DispatchProxy` 之上，形成所有生成代理共享的同一拦截核心：

- `AspectOrientedAttribute` 标记某个 `partial` 类中需要经由代理访问的成员，`IAspectOriented` 是每个生成 AOP 接口继承的标记契约。
- `ProxyMembers` 选择一次注册写入哪张钩子表，`ProxyHandler` 是 `start`、`coverage`、`end` 三段钩子共用的签名。
- `ProxyEx.CreateProxy`（通常经由生成的 `Aop()` 进入）创建由 `ProxyInstance` 支撑的 `DispatchProxy`；`ProxyEx.SetProxy` 为单个成员挂接 `(start, coverage, end)` 三元组。
- `Aop` 维护用于逆向查找的弱代理 → 目标映射；`AopCache` 为每个目标实例缓存一个代理。

## 子页面

- [AspectOrientedAttribute 与 IAspectOriented](00_特性与标记/index.md) —— 声明面。
- [ProxyMembers 与 ProxyHandler](01_代理成员处理器/index.md) —— 如何选定钩子目标，以及钩子签名。
- [ProxyEx](02_proxyex/index.md) —— 代理创建与钩子注册。
- [ProxyInstance](03_proxyinstance/index.md) —— 共享的 `DispatchProxy` 与其分发规则。
- [Aop 与 AopCache](04_代理生命周期/index.md) —— 代理 → 目标逆向查找与按实例的代理缓存。

面向用户的入口 `Aop(this T)` 是生成产物，不属于本命名空间；参见 [生成器产物](../01_生成的API/index.md)。
