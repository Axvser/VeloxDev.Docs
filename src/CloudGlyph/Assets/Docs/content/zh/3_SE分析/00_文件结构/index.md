# 00 · 文件结构

## 仓库布局

```text
VeloxDev/
├── Src/
│   ├── Core/
│   │   ├── VeloxDev.Core/                 ← 核心引擎（多目标）
│   │   │   ├── WorkflowSystem/            ← 工作流：Templates / StandardEx / CompilerEx / SelectorEx
│   │   │   ├── TransitionSystem/          ← 动画引擎：Events / Effects / Binding / Sampling / State / Runtime / NativeSamplers
│   │   │   ├── DynamicTheme/              ← 主题切换（ThemeManager / ThemeCache）
│   │   │   ├── MVVM/                      ← VeloxProperty / VeloxCommand 运行时
│   │   │   ├── Serialization/             ← 归档引擎（VeloxJson* / Archivable / Archive）
│   │   │   ├── AspectOriented/            ← AOP 代理（#if NET）
│   │   │   ├── AI/                        ← Agent 特性与反射工具
│   │   │   ├── TimeLine/                  ← Tickable 帧循环（TickManager）
│   │   │   ├── WeakTypes/                 ← WeakQueue / WeakStack / WeakCache / WeakDelegate
│   │   │   └── Interfaces/                ← 公共契约
│   │   ├── VeloxDev.Core.Extension/       ← Workflow Agent、MCP、编译图与检查点文档
│   │   ├── VeloxDev.Core.Test/            ← MSTest 单元测试
│   │   └── VeloxDev.Core.Extension.Test/  ← Extension 测试
│   ├── Adapters/                          ← 七家 GUI 适配器
│   │   ├── VeloxDev.WPF/                  ← WPF
│   │   ├── VeloxDev.Avalonia/             ← Avalonia
│   │   ├── VeloxDev.WinUI/                ← WinUI 3
│   │   ├── VeloxDev.MAUI/                 ← .NET MAUI
│   │   ├── VeloxDev.WinForms/             ← Windows Forms
│   │   ├── VeloxDev.Razor/                ← Razor / Blazor
│   │   └── VeloxDev.Jalium/               ← Jalium
│   ├── Generators/
│   │   └── VeloxDev.Core.Generator/       ← Roslyn 源生成器（WorkflowBuilder / MVVM / Command / AOP / Theme / Tickable）
│   └── Templates/                         ← dotnet new 项模板（七家平台）
├── Examples/                              ← 示例（主要证据）
│   ├── Workflow/   七家 GUI + Common/Lib
│   ├── Transition/ 七家 GUI
│   ├── Theme/      WPF · Avalonia
│   ├── MVVM/       WPF · Avalonia
│   ├── AOP/        WPF · Avalonia
│   └── Tickable/   WPF
├── Docs/
│   └── VeloxDev.Docs/                     ← CloudGlyph Wiki 子仓库
├── Assets/
└── VeloxDev.slnx
```

## 项目 → 目录

| 项目 | 路径 | 角色 |
|---|---|---|
| `VeloxDev.Core` | `Src/Core/VeloxDev.Core` | 全部功能核心；多目标 `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0` |
| `VeloxDev.Core.Extension` | `Src/Core/VeloxDev.Core.Extension` | Workflow Agent、MCP、序列化扩展；`netstandard2.0;net8.0` |
| `VeloxDev.Core.Generator` | `Src/Generators/VeloxDev.Core.Generator` | Roslyn 增量生成器（分析器包，`netstandard2.0`） |
| `VeloxDev.WPF` | `Src/Adapters/VeloxDev.WPF` | WPF 适配器 |
| `VeloxDev.Avalonia` | `Src/Adapters/VeloxDev.Avalonia` | Avalonia 适配器 |
| `VeloxDev.WinUI` | `Src/Adapters/VeloxDev.WinUI` | WinUI 3 适配器 |
| `VeloxDev.MAUI` | `Src/Adapters/VeloxDev.MAUI` | .NET MAUI 适配器 |
| `VeloxDev.WinForms` | `Src/Adapters/VeloxDev.WinForms` | Windows Forms 适配器 |
| `VeloxDev.Razor` | `Src/Adapters/VeloxDev.Razor` | Razor / Blazor 适配器 |
| `VeloxDev.Jalium` | `Src/Adapters/VeloxDev.Jalium` | Jalium 适配器（单目标 `net10.0`，平台中立） |
| `VeloxDev.*.Templates` | `Src/Templates` | `dotnet new` 项模板 |

更细的适配器内部布局与模块职责见 `01_功能结构` 及各模块的 `02_设计模式` / `03_数据流` 页面。
