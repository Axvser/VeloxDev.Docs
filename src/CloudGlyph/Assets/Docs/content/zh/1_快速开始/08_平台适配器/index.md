# 平台适配器 — 快速开始

## 平台适配器

### 概览

VeloxDev 的**工作流引擎**（`VeloxDev.Core`）与 UI 框架无关：树模型（`IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel`）、`WorkflowBuilder.Tree` 源生成器以及空间/编译机制都不关心底层是 WPF 还是 MAUI。**平台适配器**就是把该引擎变成某个 GUI 框架上真正可交互编辑器的薄层。

VeloxDev 提供**七个适配器**，每个都是独立的 NuGet 包，并配套一个 `dotnet new` 模板包：

| 适配器包 | GUI 框架 | 模板包 | 模板前缀 |
|---|---|---|---|
| `VeloxDev.WPF` | Windows Presentation Foundation | `VeloxDev.WPF.Templates` | `wpf-v-*` |
| `VeloxDev.WinForms` | Windows Forms | `VeloxDev.WinForms.Templates` | `winforms-v-*` |
| `VeloxDev.Avalonia` | Avalonia 11 | `VeloxDev.Avalonia.Templates` | `ava-v-*` |
| `VeloxDev.WinUI` | WinUI 3（Windows App SDK） | `VeloxDev.WinUI.Templates` | `winui-v-*` |
| `VeloxDev.MAUI` | .NET MAUI | `VeloxDev.MAUI.Templates` | `maui-v-*` |
| `VeloxDev.Razor` | Razor / Blazor | `VeloxDev.Razor.Templates` | `razor-v-*` |
| `VeloxDev.Jalium` | Jalium UI | `VeloxDev.Jalium.Templates` | `jalium-v-*` |

每个适配器按框架提供：

- **工作流附加行为** — 位于 `VeloxDev.WorkflowSystem.AttachedBehaviors` 命名空间：`WorkflowSurfaceBehavior`（平移/缩放/滚动宿主）、`WorkflowCanvasTransformBehavior`（共享的画布变换）、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`，以及对象池化的视图容器（绑定 `Helper.VisibleItems` 的 `ViewPool`，由 `ViewManager` 复用）。具体文件集随框架而定——例如 MAUI 通过 `WorkflowLinkOverlay` 走连线层、没有独立的画布变换行为；Razor 把若干实现写成 `.razor` 组件。
- **网格与小地图契约** — Core 共享接口 `IWorkflowGridDecorator` 与 `IWorkflowMinimapOverlay`（命名空间 `VeloxDev.WorkflowSystem`），表面行为每次渲染都会把滚动/内容偏移写入；`WorkflowMinimapOverlay` 提供默认小地图逻辑与拖拽导航。
- **过渡与主题接线** — `VeloxDev.TransitionSystem` 下的各框架封闭类型（`Interpolator`、`State`、`Transition`、`TransitionEffects`、`TransitionInterpreter`、`TransitionScheduler`、`UIThreadInspector`），以及在框架需要适配器专属值类型时、`VeloxDev.DynamicTheme` 下的平台转换器（`ColorConverter`、`BrushConverter`、`CornerRadiusConverter` 等；Jalium 的 `PlatformAdapters` 目前没有定义转换器集）。

**模板包**（`VeloxDev.{Platform}.Templates`）在每个平台都会搭出同样的「七视图套件」——节点 / 槽 / 连线 / 树 / 模板选择器 / 网格装饰层 / 小地图覆盖层，且行为已经接好。本快速开始完整走一遍 **WPF** 路径（它有最完整的演示与模板套件）；其它适配器暴露相同的类型名与命名空间，用各自前缀与框架宿主即可套用同样的步骤。

### 页面范围

WPF 是被实际演练的路径。凡是非 WPF 细节只能从源码推断（没有演示演练过），页面都会标注为 `*推断所得*`。

## 快速开始 — 子页面

- [00 前置条件](00_前置条件/index.md) — 各适配器 `.csproj` 声明的目标框架、SDK/工作负载、演示
- [01 安装与引入依赖](01_安装/index.md) — 七个适配器包与各自的模板包
- [02 配置 — 生成七个视图](02_环境配置/index.md) — 运行 `wpf-v-*` 项模板并查看每个文件接了什么
- [03 核心用法](03_核心用法/index.md) — 宿主表面、`ViewPool` 虚拟化、拖拽节点、连接槽、网格/小地图、主题接线
- [04 验证](04_验证/index.md) — 可观测结果与仓库内可运行的演示
- [05 完整代码](05_完整代码/index.md) — 精确的生成脚手架，每个源文件一页
