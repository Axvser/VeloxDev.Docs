# AOP — API 参考

> **证据来源：** Demo（`Examples/AOP/WPF/Demo`、`Examples/AOP/Avalonia/Demo`）+ 运行时源码（`Src/Core/VeloxDev.Core/AspectOriented/*.cs`、`Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`）+ 生成器源码（`Src/Generators/VeloxDev.Core.Generator/AopInterface.cs`、`AopProxy.cs`、`Writers/AopWriter.cs`）。
> **关于测试的说明：** 目前 `VeloxDev.Core.Test` 下**没有** AOP 专项测试套件（Feature Inventory 中 AOP 的 `Demo + Test` 标记已过期）。下文所有签名均来自 Demo 用法与运行时 / 生成器源码。

## API — Sections

This feature's API reference is split into:

- `00_aspect-oriented/`
- `01_generated-api/`
