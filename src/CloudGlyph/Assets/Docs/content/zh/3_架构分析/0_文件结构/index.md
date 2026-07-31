# 文件结构

## 仓库布局

```
VeloxDev/
├── Src/
│   ├── Core/
│   │   ├── VeloxDev.Core/                 ← 核心引擎（多目标框架）
│   │   │   ├── WorkflowSystem/            ← 工作流编辑器：Templates、StandardEx、Compilation、SelectorEx
│   │   │   ├── TransitionSystem/          ← 动画引擎 + NativeInterpolators/
│   │   │   ├── DynamicTheme/              ← 主题切换（ThemeManager、ThemeCache）
│   │   │   ├── MVVM/                      ← VeloxProperty/VeloxCommand 运行时 + IVeloxCommand
│   │   │   ├── AspectOriented/            ← AOP 代理（#if NET）
│   │   │   ├── AI/                        ← Agent 特性 + 反射工具
│   │   │   ├── TimeLine/                  ← MonoBehaviour 帧循环（MonoBehaviourManager）
│   │   │   ├── WeakTypes/                 ← WeakQueue/WeakStack/WeakCache/WeakDelegate
│   │   │   └── Interfaces/                ← 公共 API 契约（WorkflowSystem、TransitionSystem...）
│   │   ├── VeloxDev.Core.Extension/       ← Workflow Agent（AI.Workflow）、MCP、ComponentModelEx 序列化
│   │   ├── VeloxDev.Core.Test/            ← MSTest 单元测试
│   │   └── VeloxDev.Core.Extension.Test/  ← 扩展单元测试
│   ├── Adapters/                          ← 各 GUI 适配器
│   │   ├── VeloxDev.WPF/                  ← WPF（Attached/Workflow 行为、PlatformAdapters）
│   │   ├── VeloxDev.Avalonia/             ← Avalonia
│   │   ├── VeloxDev.WinUI/                ← WinUI 3
│   │   ├── VeloxDev.MAUI/                 ← .NET MAUI
│   │   ├── VeloxDev.WinForms/             ← Windows Forms
│   │   └── VeloxDev.Razor/                ← Razor / Blazor
│   ├── Generators/
│   │   └── VeloxDev.Core.Generator/       ← Roslyn 源生成器（WorkflowBuilder、MVVM、Command、AOP、Theme、MonoBehaviour）
│   └── Templates/                         ← dotnet new 项模板（WPF/Avalonia/MAUI/WinUI）
├── Examples/                              ← 示例（主要证据）
│   ├── Workflow/   WPF · Avalonia · WinUI · MAUI · WinForms · Blazor + Common/Lib
│   ├── Transition/ WPF · Avalonia · WinUI · WinForms · MAUI · Blazor
│   ├── Theme/      WPF · Avalonia
│   ├── MVVM/       WPF · Avalonia
│   ├── AOP/        WPF · Avalonia
│   └── MonoBehaviour/ WPF
├── Docs/
│   └── VeloxDev.Docs/                     ← CloudGlyph Wiki 仓库（content、skills、app）
├── Assets/                                ← 共享资源
├── TestResults/                           ← 测试输出
└── VeloxDev.slnx
```

## 项目到目录映射

| 项目 | 路径 | 职责 |
|---|---|---|
| `VeloxDev.Core` | `Src/Core/VeloxDev.Core` | 全部功能核心；多目标 `netstandard2.0; netframework4.6.1; net5.0; netcoreapp3.0` |
| `VeloxDev.Core.Extension` | `Src/Core/VeloxDev.Core.Extension` | Workflow Agent（AI 工具）、MCP scope、JSON 序列化（`netstandard2.0`） |
| `VeloxDev.Core.Generator` | `Src/Generators/VeloxDev.Core.Generator` | Roslyn 增量生成器（分析器包，`netstandard2.0`） |
| `VeloxDev.WPF` | `Src/Adapters/VeloxDev.WPF` | WPF 适配器（`UseWPF`） |
| `VeloxDev.Avalonia` | `Src/Adapters/VeloxDev.Avalonia` | Avalonia 适配器 |
| `VeloxDev.WinUI` | `Src/Adapters/VeloxDev.WinUI` | WinUI 3 适配器（`UseWinUI`） |
| `VeloxDev.MAUI` | `Src/Adapters/VeloxDev.MAUI` | .NET MAUI 适配器（`UseMaui`） |
| `VeloxDev.WinForms` | `Src/Adapters/VeloxDev.WinForms` | Windows Forms 适配器（`UseWindowsForms`） |
| `VeloxDev.Razor` | `Src/Adapters/VeloxDev.Razor` | Razor/Blazor 适配器（Razor SDK） |
| `VeloxDev.*.Templates` | `Src/Templates` | `dotnet new` 项模板 |

## 适配器内部布局（`VeloxDev.Avalonia` 示例）

```
VeloxDev.Avalonia/
├── Attached/Workflow/               ← XAML 附加行为（命名空间 VeloxDev.WorkflowSystem.AttachedBehaviors）
│   ├── WorkflowSurfaceBehavior.cs   ← 表面宿主、平移、视口 → Helper.Viewport
│   ├── WorkflowNodeDragBehavior.cs  ← 拖拽 → MoveCommand
│   ├── WorkflowSlotConnectionBehavior.cs ← 按下/松开 → Send/ReceiveConnectionCommand
│   ├── WorkflowSlotLayoutBehavior.cs ← 布局后重算槽位锚点
│   ├── WorkflowCanvasTransformBehavior.cs
│   ├── ViewPool.cs / ViewManager.cs ← 池化虚拟化 ItemsSource
│   ├── WorkflowMinimapOverlay.cs
│   └── IWorkflowGridDecorator.cs / IWorkflowMinimapOverlay.cs
├── PlatformAdapters/                ← Transition/Theme 平台接线
│   ├── Interpolator.cs / InterpolatorOutput.cs
│   ├── Interpolators/               ← 按类型插值器（IBrush、ITransform、BoxShadows...）
│   ├── Transition.cs / TransitionScheduler.cs / TransitionInterpreter.cs
│   ├── TransitionEffect.cs / TransitionEffects.cs / State.cs
│   ├── ThemeValueConverters.cs
│   └── UIThreadInspector.cs
└── GlobalUsings.cs
```

## 核心引擎依赖

```mermaid
flowchart LR
    subgraph Core [VeloxDev.Core]
        WF[WorkflowSystem] --> GEN[VeloxDev.Core.Generator<br/>源生成器]
        MV[MVVM] --> GEN
        TH[DynamicTheme] --> GEN
        TR[TransitionSystem] --> WD[WeakTypes.WeakDelegate]
        AI[AI 工具] --> MV
    end
    EXT[VeloxDev.Core.Extension] --> Core
    EXT --> MCP[ModelContextProtocol]
    EXT --> EXAI[Microsoft.Extensions.AI]
    EXT --> NJ[Newtonsoft.Json]
    WPF[VeloxDev.WPF] --> Core
    AV[VeloxDev.Avalonia] --> Core
    WU[VeloxDev.WinUI] --> Core
    MA[VeloxDev.MAUI] --> Core
    WF2[VeloxDev.WinForms] --> Core
    RA[VeloxDev.Razor] --> Core
```
