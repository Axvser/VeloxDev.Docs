# 动态主题 — 安装与依赖

## 1. 添加引擎核心

主题引擎位于 `VeloxDev.Core`。添加它会一并引入 `VeloxDev.Core.Generator` —— 构建期源生成器，负责把带 `[ThemeConfig]` 的 `partial` 类转换成 `IThemeObject` 实现：

```bash
dotnet add package VeloxDev.Core
```

**预期结果：** 包出现在 `.csproj` 中；还原后 `using VeloxDev.DynamicTheme;` 可编译，`ThemeManager`、`ThemeCache`、`[ThemeConfig]`、`ITheme`、`Dark` 与 `Light` 都能解析。

## 2. 为 UI 值添加平台适配器

把主题值真正应用到 UI 元素上并做动画切换，需要与你 GUI 框架匹配的适配器。适配器提供各框架的**主题值转换器**（`BrushConverter`、`ColorConverter`、`ThicknessConverter`、`DoubleConverter`、`PointConverter`、`CornerRadiusConverter`、`ObjectConverter`），以及带动画切换所用的 `Interpolator` 与 `TransitionEffects`：

```bash
dotnet add package VeloxDev.WPF       # WPF
dotnet add package VeloxDev.Avalonia  # Avalonia
```

适配器属于 VeloxDev 的 Platform Adapters 系列包；每个适配器都引用 `VeloxDev.Core`，因此实践中只需引用适配器即可（WPF 示例只引用了 `VeloxDev.WPF` 工程）。

**预期结果：** `BrushConverter` 可作为 `[ThemeConfig]` 的转换器类型使用；在 `VeloxDev.TransitionSystem` 下能解析适配器的 `Interpolator` 与 `TransitionEffects.Theme`。

## 3. 仓库内方案（Debug 工程引用）

不通过 NuGet、而是对照仓库源码构建时，只引用适配器工程即可 —— 示例正是如此：

```xml
<ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Adapters\VeloxDev.WPF\VeloxDev.WPF.csproj" />
</ItemGroup>
```

适配器工程在 `Debug` 下引用 `VeloxDev.Core` **工程**（`Release` 下引用 `VeloxDev.Core` **NuGet 包**），因此主题引擎与源生成器会传递地流入你的工程。

**预期结果：** 工程能还原并构建；带 `[ThemeConfig]` 的 `partial` 类在编译期获得生成的 `IThemeObject` 成员。
