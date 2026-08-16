# 平台适配器 — 快速开始

## 平台适配器

### 快速开始

VeloxDev 提供六个 GUI 适配器 — **WPF**、**Avalonia**、**WinUI**、**MAUI**、**WinForms** 和 **Razor（Blazor）** — 每个都有独立包（`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor`）。适配器是把与 UI 框架无关的工作流引擎变成真正可交互编辑器的那一层：它提供驱动画布的附加行为（attached behaviors）、对象池化的视图容器、小地图/网格装饰层接口，以及各平台的过渡与主题接线（`Interpolator`、`TransitionEffects`、`ThemeValueConverters`、`UIThreadInspector`）。

一套 `dotnet new` 项模板套件（`VeloxDev.WPF.Templates` 及同级包）可以直接生成 Node / Slot / Link / Tree / 模板选择器 / 网格装饰层 / 小地图覆盖层视图，且行为已经接好。

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages:

- `00_prerequisites/`
- `01_install/`
- `02_setup/`
- `03_core-usage/`
- `04_verification/`
- `05_complete-code/` — the complete scaffold, one page per source file
