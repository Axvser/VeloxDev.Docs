# 运行时主题

`VeloxDev.DynamicTheme` 声明主题化属性、为每个属性保存每个主题的值，并瞬时或经过渡引擎切换当前主题。声明是生成的：分部类上的 `[ThemeConfig<…>]` 特性使生成器产出 `InitializeTheme`、`SetThemeValue`、`RestoreThemeValue`、两个生命周期钩子与两个缓存访问器。

主题值由平台的 `IThemeValueConverter` 转换一次。切换随后采样已转换并缓存的值，不再运行转换器。

## 类型分组

| 分组 | 类型 | 页面 |
|---|---|---|
| 声明与存储 | `ThemeConfigAttribute<…>`、`ITheme`、`IThemeObject`、`IThemeValueConverter`、`Light`、`Dark`、`ThemeCache`、生成成员 | [声明与类型](00_声明与类型/index.md) |
| 切换 | `ThemeManager`、`StartModel` | [主题管理器](01_主题管理器/index.md) |
| 平台转换器 | `BrushConverter`、`ColorConverter`、`ObjectConverter` 及各平台转换器集 | [平台转换器](02_平台转换器/index.md) |

## 切换模型

- `ThemeManager.Transition<T>(effect)` 在共享时间轴上把所有已注册对象动画到主题 `T`。
- `ThemeManager.Jump<T>()` 一次性写入所有终值，不需要插值器或效果。
- `ThemeManager.SetCurrent<T>()` 只改变 `ThemeManager.Current`，不触碰任何已注册对象。

当前主题默认为 `Dark`。`ThemeManager.Current` 由过渡与跳变路径内部赋值，因此一次落地的切换才会推进它。

可运行的窗口见[运行时主题快速开始](../../1_快速开始/13_运行时主题/index.md)。

## 要求

- 生成成员需要 `VeloxDev.Core.Generator`。
- 动画切换需要适配器的过渡表面，并调用一次 `ThemeManager.SetPlatformInterpolator(new Interpolator())`；没有它切换仍会落地，但会跳变。
- `[ThemeConfig]` 要求类是 `partial`；非分部类不会产出任何内容。
