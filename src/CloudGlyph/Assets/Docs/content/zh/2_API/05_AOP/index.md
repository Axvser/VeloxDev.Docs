# AOP — API 参考

功能：为 `.NET` 目标提供动态切面（AOP）代理。`AspectOrientedAttribute` 标记某个 `partial` 类的成员；Roslyn 源生成器为其生成 AOP 代理接口与 `Aop(this T)` 扩展；运行时命名空间 `VeloxDev.AspectOriented` 构建 `DispatchProxy` 代理，并允许按成员附加 `start` / `coverage` / `end` 三段钩子，无需改动模型源码即可观察或替换原始逻辑。

**公开面一览**

- 运行时 —— 命名空间 `VeloxDev.AspectOriented`（`#if NET`）：`AspectOrientedAttribute`、`IAspectOriented`、枚举 `ProxyMembers`、委托 `ProxyHandler`、静态 `ProxyEx`、`ProxyInstance : DispatchProxy`、静态 `Aop`、静态 `AopCache`。
- 生成产物 —— 接口 `VeloxDev.AopInterfaces.{Class}_{Ns}_Aop` 与入口点 `{Class}_{Ns}_AopExtensions.Aop(this T)`。

**证据来源**

- Demo：`Examples/AOP/WPF/Demo`、`Examples/AOP/Avalonia/Demo`。
- 运行时源码：`Src/Core/VeloxDev.Core/AspectOriented/*.cs` 与 `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`。
- 生成器源码：`Src/Generators/VeloxDev.Core.Generator/AopInterface.cs`、`AopProxy.cs`、`Writers/AopWriter.cs`。
- **测试说明：** 刷新时 `VeloxDev.Core.Test` 下尚无 AOP 专项套件（Feature Inventory 中该功能的 `Demo + Test` 条目在 Test 一半上已过期）。以下公开面已对照 Demo 与运行时 / 生成器源码核验。

## API — 章节

- [AOP 运行时 —— 命名空间 `VeloxDev.AspectOriented`](00_面向切面/index.md) —— 标记特性、标记接口、钩子契约、代理工厂 / 实例与生命周期缓存。
- [生成器产物（源生成器）](01_生成的API/index.md) —— 编译期生成的 AOP 接口、partial 类胶水与 `Aop(this T)` 扩展。
