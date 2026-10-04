# 过渡动画 — 安装依赖

## 1. 添加引擎内核

每个过渡应用都引用 `VeloxDev.Core`。把它加进任意 .NET 项目：

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core` 包含全部与框架无关的东西：`Eases` 与 `Ease*` 类、采样器注册表（`InterpolatorCore` + `NativeSamplers/*`）、`TransitionEffectCore`、调度器/解释器（含 `FramePacerCore` 节奏基类）、开放泛型构建器基类 `TransitionCore<...>` / `StateSnapshotCore<...>`、`TransitionCoreEx` 链式扩展、时间层（`VeloxDev.Timing`），以及宿主接缝（`VeloxDev.Threading` / `VeloxDev.Lifetime`）。这里没有任何东西依赖 GUI 框架。

**预期结果：** 包出现在 `.csproj` 中；还原后 `using VeloxDev.TransitionSystem;` 可解析，且 `Eases.Cubic.InOut.Ease(0.5)` 能在普通控制台里运行。`using VeloxDev.Timing;` 同样可解析，因此一个无头时钟完全不需要适配器就能用（见[时间层](../07_时间层/index.md)）。

## 2. 为 UI 绑定属性添加平台适配器

动画化 **UI 绑定属性**需要你 GUI 框架对应的适配器。适配器在同一命名空间下重新给出封闭、友好的类型（`Transition`、`Transition<T>`、`State`、`TransitionEffect`、`TransitionEffects`、`Interpolator`、`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`），注册按框架的值采样器，并把每一帧写入编组到 UI 线程：

```bash
dotnet add package VeloxDev.WPF      # WPF
dotnet add package VeloxDev.Avalonia # Avalonia
dotnet add package VeloxDev.WinUI    # WinUI 3
dotnet add package VeloxDev.MAUI     # .NET MAUI
dotnet add package VeloxDev.WinForms # Windows Forms
dotnet add package VeloxDev.Razor    # Blazor（Razor 组件）
```

适配器包属于 VeloxDev 的平台适配器套件；每一个都在 `VeloxDev.Core` 之上携带自己的按框架过渡 / 主题接线（`Interpolator`、`TransitionEffect(s)`、`UIThreadInspector` 等）。

**预期结果：** 对应的包已被引用；`Transition<Rectangle>.Create()` 能编译（WPF 例子），且 WPF 专属采样器（`Brush`、`Color`、`Transform`、`CornerRadius`、`Thickness`、`Point3D` 等）已注册。

## 3. 什么时候可以跳过适配器？

当你直接驱动原语、且值不需要 UI 线程编组时，引擎内核就够了 —— 这正是 `Src/Core/VeloxDev.Core.Test/TransitionSystem/SamplingLoopTests.cs` 所演练的模式（一个持有 `double` 目标的 `StateCore`、一个 `TransitionEffectCore`、一个派生自 `InterpolatorCore` 的生产者，以及一个就地施加帧的解释器）。这就是「过渡对非 UI 值不需要适配器」的含义。

不过开箱即用的 `Transition<T>` 构建器由各适配器包提供，因此通向顶层 API 的最简路径 —— 包括目标只是运行中应用里的普通对象时 —— 就是引用你框架的适配器。UI 绑定目标还会额外要求适配器，好让属性写入被派发到所属 UI 线程（见 [UI 线程与编组](../06_UI线程与编组/index.md)）。

有**两件事完全不需要任何适配器**：经内核原语驱动的纯值插值，以及整个 `VeloxDev.Timing` 层 —— 时间源、采样器与停摆信号都在 `VeloxDev.Core` 里（见[时间层](../07_时间层/index.md)）。
