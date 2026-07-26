# 文件结构

## 仓库布局

```
VeloxDev/
├── Src/
│   ├── Core/
│   │   ├── VeloxDev.Core/                 ← 核心引擎 (netstandard2.0, net4.6.1, net5, netcoreapp3.0)
│   │   │   ├── WorkflowSystem/            ← 工作流编辑引擎
│   │   │   ├── TransitionSystem/          ← 属性动画系统
│   │   │   ├── DynamicTheme/              ← 动态主题切换
│   │   │   ├── MVVM/                      ← MVVM 基础设施
│   │   │   ├── AspectOriented/            ← AOP 代理系统
│   │   │   ├── AI/                        ← AI Agent 集成
│   │   │   ├── TimeLine/                  ← MonoBehaviour 系统
│   │   │   ├── WeakTypes/                 ← 弱引用集合
│   │   │   └── Interfaces/                ← 公共 API 接口
│   │   ├── VeloxDev.Core.Extension/       ← 可选扩展（AI/MCP/工作流资源）
│   │   ├── VeloxDev.Core.Test/            ← MSTest 单元测试
│   │   └── VeloxDev.Core.Generator/       ← Roslyn 源生成器
│   ├── Adapters/
│   │   ├── VeloxDev.WPF/                  ← WPF 适配器
│   │   ├── VeloxDev.Avalonia/             ← Avalonia 适配器
│   │   ├── VeloxDev.WinUI/               ← WinUI 适配器
│   │   ├── VeloxDev.MAUI/                ← .NET MAUI 适配器
│   │   ├── VeloxDev.WinForms/            ← Windows Forms 适配器
│   │   └── VeloxDev.Razor/               ← Blazor/Razor 适配器
│   └── Templates/                         ← 项目模板
├── Examples/
│   ├── Workflow/                          ← 工作流示例（所有平台）
│   ├── Transition/                        ← 动画示例（所有平台）
│   ├── Theme/                             ← 主题示例
│   ├── MVVM/                              ← MVVM 示例
│   ├── AOP/                               ← AOP 示例
│   └── MonoBehaviour/                     ← MonoBehaviour 示例
├── Docs/
│   └── VeloxDev.Docs/                     ← Wiki 文档（CloudGlyph）
└── Assets/                                ← 共享资源（logo, 图标）
```

## 核心模块结构（`VeloxDev.Core`）

```
VeloxDev.Core/
├── Interfaces/WorkflowSystem/      ← 公共 API 契约
│   ├── IWorkflowTreeViewModel.cs
│   ├── IWorkflowNodeViewModel.cs
│   ├── IWorkflowSlotViewModel.cs
│   ├── IWorkflowLinkViewModel.cs
│   └── ...（helpers, spatial 等）
├── WorkflowSystem/                  ← 实现
│   ├── Anchor.cs / Size.cs / Offset.cs / Viewport.cs / CellKey.cs
│   ├── CanvasLayout.cs / WorkContext.cs / NodeBoundsProvider.cs
│   ├── SpatialGridHashMap.cs       ← 空间索引
│   ├── WorkflowSpatialManager.cs   ← 空间管理
│   ├── WorkflowActionPair.cs       ← 撤销/重做操作
│   ├── Templates/                  ← 构建器属性 + 默认 ViewModel
│   │   ├── WorkflowBuilder.cs      ← [Tree<T>], [Node<T>], [Slot<T>], [Link<T>]
│   │   ├── ViewModels/             ← 默认 ViewModel 实现
│   │   └── Helpers/                ← 默认 Helper 实现
│   ├── StandardEx/                 ← 标准扩展方法
│   ├── Compilation/                ← 工作流编译器
│   └── SelectorEx/                 ← 条件槽位选择器
├── TransitionSystem/               ← 动画引擎
├── DynamicTheme/                   ← 主题系统
├── MVVM/                           ← VeloxCommand, 属性
├── AI/                             ← Agent 集成
├── AspectOriented/                 ← AOP
├── TimeLine/                       ← MonoBehaviour
└── WeakTypes/                      ← 弱引用集合
```

## 适配器结构（例如 `VeloxDev.Avalonia`）

```
VeloxDev.Avalonia/
├── Attached/Workflow/              ← XAML 附加行为
│   ├── WorkflowSurfaceBehavior.cs
│   ├── WorkflowNodeDragBehavior.cs
│   ├── WorkflowSlotConnectionBehavior.cs
│   ├── WorkflowSlotLayoutBehavior.cs
│   ├── WorkflowCanvasTransformBehavior.cs
│   ├── ViewPool.cs / ViewManager.cs
│   └── WorkflowMinimapOverlay.cs
├── PlatformAdapters/               ← 平台特定实现
│   ├── Interpolator.cs / InterpolatorOutput.cs
│   ├── Interpolators/              ← 类型特定插值器
│   ├── Transition.cs / TransitionScheduler.cs
│   ├── TransitionEffect.cs
│   ├── State.cs
│   ├── ThemeValueConverters.cs
│   └── UIThreadInspector.cs
└── GlobalUsings.cs
```
