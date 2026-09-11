# Transition — 安装 / 添加依赖

## 1. 添加引擎核心

每个 Transition 应用都引用 `VeloxDev.Core`。把它加入任意 .NET 项目：

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core` 包含与框架无关的引擎：`Eases` 与 `Ease*` 类、采样器注册表（`InterpolatorCore` + `NativeSamplers/*`）、`TransitionEffectCore`、调度器/解释器与状态描述机制。这里没有任何东西依赖 GUI 框架。

**预期结果：** 包写入 `.csproj`；还原后 `using VeloxDev.TransitionSystem;` 可解析，`Eases.Cubic.InOut.Ease(0.5)` 在纯控制台即可运行。

## 2. 为 UI 绑定属性添加平台适配器

**动画 UI 绑定的属性**需要你 GUI 框架对应的适配器。适配器在相同命名空间下重新导出封闭的便捷类型（`Transition`、`Transition<T>`、`State`、`TransitionEffect`、`TransitionEffects`、`Interpolator`、`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`），注册框架专属值采样器，并把每一帧写入编组到 UI 线程：

```bash
dotnet add package VeloxDev.WPF      # WPF
dotnet add package VeloxDev.Avalonia # Avalonia
dotnet add package VeloxDev.WinUI    # WinUI 3
dotnet add package VeloxDev.MAUI     # .NET MAUI
dotnet add package VeloxDev.WinForms # Windows Forms
dotnet add package VeloxDev.Razor    # Blazor（Razor 组件）
```

这些适配器包隶属于 VeloxDev 的平台适配器套件；每个适配器在 `VeloxDev.Core` 之上自带框架专属的过渡/主题接线（`Interpolator`、`TransitionEffect(s)`、`UIThreadInspector` …）。

**预期结果：** 匹配的包被引用后，`Transition<Rectangle>.Create()` 可编译（以 WPF 为例），且 WPF 专属采样器（`Brush`、`Color`、`Transform`、`CornerRadius`、`Thickness`、`Point3D` …）已注册。

## 3. 何时可以省略适配器

当你直接驱动底层原语、且值无需 UI 线程编组时，仅引擎核心就足够 —— 这正是 `Src/Core/VeloxDev.Core.Test/TransitionSystem/SamplingLoopTests.cs` 所演练的模式（持有 `double` 目标的 `StateCore`、一个 `TransitionEffectCore`、一个 `InterpolatorCore` 派生生产者、以及一个内联应用帧的解释器）。这就是「非 UI 值动画无需适配器」的含义。

不过，开箱即用的 `Transition<T>` 构建器由各适配器包提供，因此使用顶层 API 的最简路径 —— 包括动画运行中的应用内普通对象 —— 仍是引用你框架的适配器。UI 绑定目标还必须依赖适配器，使属性写入分发到其所属 UI 线程（见 [UI线程与编组](../06_UI线程与编组/index.md)）。
