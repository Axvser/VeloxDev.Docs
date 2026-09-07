# 平台适配器 — API 参考

平台适配器（platform adapter）是把「与 UI 框架无关」的 VeloxDev 工作流引擎转成某个具体 UI 框架上可交互编辑器的薄层。每个适配器是一个独立的 NuGet 包（`VeloxDev.WPF`、`VeloxDev.Avalonia`、`VeloxDev.WinUI`、`VeloxDev.MAUI`、`VeloxDev.WinForms`、`VeloxDev.Razor`、`VeloxDev.Jalium`，源码在 `Src/Adapters/VeloxDev.*`），并暴露**同一组公共命名空间**，因此针对其中一个适配器编写的程序可迁移到其它平台：

| 命名空间 | 用途 |
|---|---|
| `VeloxDev.WorkflowSystem.AttachedBehaviors` | 工作流附加行为与视图容器：`WorkflowSurfaceBehavior`、`WorkflowCanvasTransformBehavior`、`ViewPool`、`ViewManager`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`、`WorkflowMinimapOverlay`，以及适配器特有类型（`WorkflowLinkOverlay`、`WorkflowGridDecorator`、`WorkflowTreeView`、`IWorkflowTemplateSelector`） |
| `VeloxDev.TransitionSystem` | 适配器提供的过渡动画表面 —— `Transition`、`Transition<T>`、`Transition<T>.StateSnapshot`、`TransitionEx`、`Interpolator`、`TransitionEffect`、`TransitionEffects`、`State`、`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`（各适配器成员在 `2_API/03_transition` 特性中记录） |
| `VeloxDev.DynamicTheme` | 主题值转换器（`BrushConverter`、`DoubleConverter`、`PointConverter`、……）。`VeloxDev.Jalium` 不提供（各适配器转换器集合在 `2_API/04_dynamic-theme` 特性中记录） |
| `VeloxDev.Adapters.NativeSamplers` | 每种框架值类型对应一个采样器类（如 `BrushSampler`、`ThicknessSampler`、`PaddingSampler`），由该适配器的 `Interpolator` 注册 |

配套的 `dotnet new` 项模板套件（`VeloxDev.{Platform}.Templates`，源码在 `Src/Templates/VeloxDev.*.Templates`）把 Node / Slot / Link / Tree / selector / grid-decorator / minimap 视图连同已接好的行为一起脚手架化。

> 证据与覆盖：每种平台的工作流 Demo 都在 `Examples/Workflow/<Platform>` 下（各带一个 `Trimmed` 兄弟目录）并引用这些行为，因此这些行为在全部七个适配器上的**名称与形态均已按源码验证**（文件：`Src/Adapters/VeloxDev.*/Attached/Workflow/*.cs`）。凡是 Demo 未实际驱动的各平台**行为细节均标记为 `*推断所得*`**（未经运行证实）。其中 WPF / Avalonia（Razor 由 Blazor Demo）覆盖最多；本页对每个此类论断逐一标注。

## 各适配器包一览

| 包 | 目标框架（取自 `.csproj`） | 使用的框架表面 |
|---|---|---|
| `VeloxDev.WPF` | `netframework4.6.1`；`net5.0-windows`；`netcoreapp3.0` | `System.Windows`（WPF） |
| `VeloxDev.Avalonia` | `netstandard2.0`；`net6.0` | Avalonia 11.1（`Avalonia.Themes.Fluent`、`Avalonia.Fonts.Inter`） |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0`；`net10.0-windows10.0.19041.0` | Microsoft.WindowsAppSDK 1.6 / WinUI 3 |
| `VeloxDev.MAUI` | `net10.0`；`net10.0-windows10.0.19041.0` | .NET MAUI 10.0（Microsoft.Maui.Controls）；Windows TFM 使用 WinUI 3 |
| `VeloxDev.WinForms` | `netframework4.6.1`；`net5.0-windows`；`netcoreapp3.0` | `System.Windows.Forms` |
| `VeloxDev.Razor` | `net6.0` | Blazor / Razor（`Microsoft.NET.Sdk.Razor`、ASP.NET Core） |
| `VeloxDev.Jalium` | `net10.0`（平台中立） | Jalium.UI.Controls（仅跨平台核心） |

七个包版本均为 `8.0.0`，依赖 `VeloxDev.Core`（`Debug` 为项目引用，其余为 `8.0.0` 包引用），并由此传递性地暴露工作流引擎、过渡动画引擎与主题层。

> 跨特性归属：**适配器提供的过渡动画类型**属于过渡动画特性（`2_API/03_transition` 的 `03_adapter-provided` 一节），**适配器主题转换器**属于动态主题特性（`2_API/04_dynamic-theme` 的 `04_PlatformAdapters` 一页）。本特性记录的是：适配器本身、它们承载的工作流附加行为表面，以及 `dotnet new` 视图模板。

## 页面

- [00_attached-behaviors](00_attached-behaviors/index.md) — `VeloxDev.WorkflowSystem.AttachedBehaviors` 中共享的工作流附加行为表面，统一记录一次并附带各适配器形态（表面与画布变换、视图池、节点/槽行为、小地图、适配器特有覆盖层）。
- [01_adapter-catalogue](01_adapter-catalogue/index.md) — 按适配器索引：每个包提供哪些行为文件、基类、原生采样器与过渡/主题接线。
- [02_templates](02_templates/index.md) — `dotnet new` 项模板及其 CLI 选项。
