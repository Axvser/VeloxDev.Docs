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
