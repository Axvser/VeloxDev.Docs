# 动态主题 — 快速入门

## 动态主题

### 概览

**动态主题** 为基于 VeloxDev 的编辑器或应用带来**带动画过渡的运行时主题切换**。你用 `[ThemeConfig]` 在控件或视图模型上把每个参与主题的属性映射为「每个主题下一个值」，然后在运行时于主题间切换 —— 通过 `ThemeManager.Transition<T>(effect)` 平滑切换（由 TransitionSystem 引擎逐帧插值），或通过 `ThemeManager.Jump<T>()` 即时切换。

该功能分两层提供：

- **引擎核心**（`VeloxDev.Core`）—— 位于 `VeloxDev.DynamicTheme` 命名空间、与框架无关的主题模型：`ThemeManager`（静态 `Current`、`StartModel`、`SetPlatformInterpolator`、`SetCurrent<T>`、`Register`/`Unregister`、`Transition<T>`、`Jump<T>`）、共享的 `ThemeCache`、`[ThemeConfig]` 特性（1 个转换器 + 2–7 个主题，共 6 个泛型元数）、标记接口 `ITheme`（含内置的 `Dark` 与 `Light`）、`IThemeObject`（源生成器契约）与 `IThemeValueConverter`。驱动主题动画的插值引擎（TransitionSystem）同样位于 `VeloxDev.Core`。
- **平台适配器层**（Platform Adapters 系列包，如 `VeloxDev.WPF`、`VeloxDev.Avalonia`）—— 各框架的**主题值转换器**（`BrushConverter`、`ColorConverter`、`ThicknessConverter`、`DoubleConverter`、`PointConverter`、`CornerRadiusConverter`、`ObjectConverter`），把 `[ThemeConfig]` 的上下文参数转换成真实 UI 值；此外还提供带动画切换所需的 `Interpolator` 子类与 `TransitionEffects` 预设。

要把主题值真正应用到 UI 元素上，需要与你 GUI 框架匹配的适配器 —— 它提供转换器与平台 `Interpolator`。官方两个示例覆盖 **WPF** 与 **Avalonia**。

权威示例位于 `Examples/Theme/{WPF,Avalonia}/Demo`，引擎契约由 `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` 锁定。

## 快速开始 — 子页面

- [00 前置条件](00_前置条件/index.md) —— 支持目标框架、SDK/工作负载、示例与测试
- [01 安装与依赖](01_安装与依赖/index.md) —— `VeloxDev.Core`（附带源生成器）+ 平台适配器
- [02 声明与注册](02_声明与注册/index.md) —— 主题类、`[ThemeConfig]` + 转换器、把类变成 `IThemeObject`
- [03 运行时切换](03_运行时切换/index.md) —— 插值器设置、`Transition` / `Jump` / `SetCurrent`、回调、运行时覆盖、UI 线程说明
- [04 验证与完整代码](04_验证与完整代码/index.md) —— 用示例与测试验证、单个可运行程序、运行声明
