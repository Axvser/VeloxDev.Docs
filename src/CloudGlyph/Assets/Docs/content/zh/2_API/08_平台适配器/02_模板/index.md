# API — 工作流视图模板

每个适配器都带一套 `dotnet new` 项模板（`VeloxDev.{Platform}.Templates`，源码在 `Src/Templates/VeloxDev.*.Templates`），把已接好行为的工作流视图脚手架化。模板用标准 `dotnet new install` 安装，以 `dotnet new <shortName> -n <ClassName>` 使用。

## 各适配器模板套件

所有套件都含同一种类七项：节点视图、槽视图、连接视图、树视图、模板选择器、网格装饰层、小地图覆盖层。短名在所有平台统一为 `{prefix}-v-{kind}`（网格装饰层 = `{prefix}-v-decorator`）。

| 包 | Node | Slot | Link | Tree | Selector | Decorator | Minimap |
|---|---|---|---|---|---|---|---|
| `VeloxDev.WPF.Templates` | `wpf-v-node` | `wpf-v-slot` | `wpf-v-link` | `wpf-v-tree` | `wpf-v-selector` | `wpf-v-decorator` | `wpf-v-minimap` |
| `VeloxDev.Avalonia.Templates` | `ava-v-node` | `ava-v-slot` | `ava-v-link` | `ava-v-tree` | `ava-v-selector` | `ava-v-decorator` | `ava-v-minimap` |
| `VeloxDev.WinUI.Templates` | `winui-v-node` | `winui-v-slot` | `winui-v-link` | `winui-v-tree` | `winui-v-selector` | `winui-v-decorator` | `winui-v-minimap` |
| `VeloxDev.MAUI.Templates` | `maui-v-node` | `maui-v-slot` | `maui-v-link` | `maui-v-tree` | `maui-v-selector` | `maui-v-decorator` | `maui-v-minimap` |
| `VeloxDev.WinForms.Templates` | `winforms-v-node` | `winforms-v-slot` | `winforms-v-link` | `winforms-v-tree` | `winforms-v-selector` | `winforms-v-decorator` | `winforms-v-minimap` |
| `VeloxDev.Razor.Templates` | `razor-v-node` | `razor-v-slot` | `razor-v-link` | `razor-v-tree` | `razor-v-selector` | `razor-v-decorator` | `razor-v-minimap` |
| `VeloxDev.Jalium.Templates` | `jalium-v-node` | `jalium-v-slot` | `jalium-v-link` | `jalium-v-tree` | `jalium-v-selector` | `jalium-v-decorator` | `jalium-v-minimap` |

## 默认名与生成文件

各模板的默认类名依次为 `NodeView`、`SlotView`、`LinkView`、`TreeView`、`TemplateSelector`、`GridDecorator`、`MinimapOverlay`（用 `-n <Name>` 指定实际名）。节点/槽/连接/树模板在 XAML 风格平台生成标记 + 代码后置对（`.xaml`/`.cs` 或 Avalonia/WinUI 等价物）；选择器/装饰层/小地图生成单个代码后置文件。Razor 生成 `.razor`（+ `.razor.cs`）。

## 七个模板出厂就是接好的

生成出来的项目不需要手工接线。**树视图是枢纽**：它托管池与各类表面行为，并按名字引用兄弟模板 —— 节点/槽/连接视图，以及**模板选择器**（池最先问的那一个）。

| 适配器 | 树视图怎么把选择器交给池 |
|---|---|
| WPF / Avalonia / WinUI / MAUI | `ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}"` —— 画布上的附加属性 |
| WinForms | `ViewPool.SetTemplateSelector(PART_Canvas, _selector)` —— 这家没有附加属性系统，只能方法调用 |
| Jalium | `ViewPool.SetTemplateSelector(this, TemplateSelector)`；该属性**自带默认值**，所以生成出来的树视图不会是「没有选择器」的 |
| Razor | 一个 `<TemplateSelector …>` 组件，它的 `ItemTemplate` 是池唯一的视图来源 |

**选择器是最高优先级的视图来源**，它在平台自己的查找**之前**被问到；有平台查找的那四家（四个 XAML 风格适配器）在它不匹配时**退回**平台查找，而 WinForms / Jalium / Razor 没有可退的东西 —— 那里选择器缺失就是**一个视图都不建、也不报错**（见[视图池](../00_附加行为/01_视图池/index.md)）。要客制化，替换生成的选择器类或那一处引用即可，**不要改池**。

## 连线右键菜单

树视图模板还声明了**连线的右键菜单**并让表面指向它。接线（右键、定位、开合、向中枢上报）归适配器，不归模板代码后置 —— 四个 XAML 家只多一个附加属性与菜单资源，Razor 传一个片段参数，纯代码的两家重写一个钩子：

| 适配器 | 声明方式 |
|---|---|
| WPF / Avalonia | 一个 `ContextMenu` 资源，键经 `WorkflowSurfaceBehavior.LinkMenuKey` 指定 |
| WinUI / MAUI | 一个 `MenuFlyout` 资源，用同样的键 |
| Razor | 表面组件上的 `<LinkMenu Context="link">…</LinkMenu>` 片段参数 |
| WinForms / Jalium | `WorkflowTreeView.OnBuildLinkMenu(menu, link)` —— 基类只加一个「Delete」条目 |

每个条目绑定它作用于的那条连线，因此增删一个动作只改模板：`MenuItem` / `MenuFlyoutItem` 写 `Command="{Binding DeleteCommand}"`，Razor 按钮写 `@onclick="() => link.DeleteCommand.Execute(null)"`。Avalonia 的菜单资源没有 `x:DataType`，在编译绑定下写 `{ReflectionBinding DeleteCommand}`。

在 Razor 上，那句 `@onclick` 之所以能绑上，是因为本库自带一个 `_Imports.razor`，内容是 `@using Microsoft.AspNetCore.Components.Web`（`Src/Adapters/VeloxDev.Razor/_Imports.razor`）。这个文件是**有承载作用的、不是装饰**：少了它，编译器会把处理器当成**字面属性**输出（`"@onclick"`），于是永不执行。消费方项目若也要编译生成出来的 Razor 视图，同样需要这条 import。

## CLI 选项（以 WPF 套件为例）

每个模板都接受 `-ns <Namespace>` 指定生成的命名空间。视图模板另声明样式参数；WPF 套件的 `dotnetcli.host.json` 映射如下：

| 模板 | 选项（短名 → 符号） |
|---|---|
| Node（`wpf-v-node`） | `-ns` namespace，`-bg` nodeBackground，`-fg` nodeForeground，`-bb` nodeBorderBrush，`-bt` nodeBorderThickness，`-cr` nodeCornerRadius |
| Slot（`wpf-v-slot`） | `-ns` namespace，`-bg` slotBackground，`-sc` slotColor，`-sp` slotPath |
| Link（`wpf-v-link`） | `-ns` namespace，`-lc` linkColor，`-lt` linkThickness |
| Tree（`wpf-v-tree`） | `-ns` namespace，`-bg` surfaceBackground，`-bb` surfaceBorderBrush，`-bt` surfaceBorderThickness |
| Selector（`wpf-v-selector`） | 仅 `-ns` namespace |
| Decorator（`wpf-v-decorator`） | `-ns` namespace，`-bg` gridBackground，`-mic` minorGridColor，`-mac` majorGridColor，`-ac` axisColor，`-gs` gridSpacing，`-mle` majorLineEvery，`-rb` rulerBackground，`-rtc` rulerTickColor，`-rlc` rulerLabelColor，`-rdc` rulerDividerColor |
| Minimap（`wpf-v-minimap`） | `-ns` namespace，`-bg` minimapBackground，`-bdr` minimapBorder，`-nf` nodeFill，`-vs` viewportStroke |

**注意：** 选项短/长名按包在每个模板的 `.template.config/dotnetcli.host.json` 中声明，**跨套件并不保证一致**（例如 WinForms 装饰层背景的长名为 `grid-background`，而非 `background`）。任一模板的确切选项列表以它自己的 `.template.config/dotnetcli.host.json` 为准；节点/槽/连接/树/小地图模板另带未在 WPF 宿主文件中作为 CLI 选项暴露的额外模板符号（如 `nodeWidth` / `nodeHeight`）。
