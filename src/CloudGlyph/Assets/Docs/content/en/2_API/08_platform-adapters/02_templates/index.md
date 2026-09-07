# API — Workflow View Templates

Each adapter ships a `dotnet new` item-template suite (`VeloxDev.{Platform}.Templates`, source under `Src/Templates/VeloxDev.*.Templates`) that scaffolds the workflow views with the behaviors already connected. Templates are installed with the standard `dotnet new install` and used with `dotnet new <shortName> -n <ClassName>`.

## Template suite per adapter

All suites contain the same seven kinds: node view, slot view, link view, tree view, template selector, grid decorator, minimap overlay. Short names are `{prefix}-v-{kind}`; the grid decorator is `{prefix}-v-decorator` on every platform **except Jalium**, where it is `jalium-v-grid`.

| Package | Node | Slot | Link | Tree | Selector | Decorator | Minimap |
|---|---|---|---|---|---|---|---|
| `VeloxDev.WPF.Templates` | `wpf-v-node` | `wpf-v-slot` | `wpf-v-link` | `wpf-v-tree` | `wpf-v-selector` | `wpf-v-decorator` | `wpf-v-minimap` |
| `VeloxDev.Avalonia.Templates` | `ava-v-node` | `ava-v-slot` | `ava-v-link` | `ava-v-tree` | `ava-v-selector` | `ava-v-decorator` | `ava-v-minimap` |
| `VeloxDev.WinUI.Templates` | `winui-v-node` | `winui-v-slot` | `winui-v-link` | `winui-v-tree` | `winui-v-selector` | `winui-v-decorator` | `winui-v-minimap` |
| `VeloxDev.MAUI.Templates` | `maui-v-node` | `maui-v-slot` | `maui-v-link` | `maui-v-tree` | `maui-v-selector` | `maui-v-decorator` | `maui-v-minimap` |
| `VeloxDev.WinForms.Templates` | `winforms-v-node` | `winforms-v-slot` | `winforms-v-link` | `winforms-v-tree` | `winforms-v-selector` | `winforms-v-decorator` | `winforms-v-minimap` |
| `VeloxDev.Razor.Templates` | `razor-v-node` | `razor-v-slot` | `razor-v-link` | `razor-v-tree` | `razor-v-selector` | `razor-v-decorator` | `razor-v-minimap` |
| `VeloxDev.Jalium.Templates` | `jalium-v-node` | `jalium-v-slot` | `jalium-v-link` | `jalium-v-tree` | `jalium-v-selector` | `jalium-v-grid` | `jalium-v-minimap` |

## Default names & generated files

Each template's default class name is `NodeView`, `SlotView`, `LinkView`, `TreeView`, `TemplateSelector`, `GridDecorator`, or `MinimapOverlay` respectively (set the actual name with `-n <Name>`). The node/slot/link/tree templates generate a markup + code-behind pair on the XAML-style platforms (`.xaml`/`.cs` or Avalonia/WinUI equivalents), while selector/decorator/minimap generate a single code-behind file. Razor generates `.razor` (+ `.razor.cs`) files.

## CLI options (WPF suite example)

Each template accepts `-ns <Namespace>` for the generated namespace. View templates additionally declare style parameters; the WPF suite's `dotnetcli.host.json` maps them as follows:

| Template | Options (short → symbol) |
|---|---|
| Node (`wpf-v-node`) | `-ns` namespace, `-bg` nodeBackground, `-fg` nodeForeground, `-bb` nodeBorderBrush, `-bt` nodeBorderThickness, `-cr` nodeCornerRadius |
| Slot (`wpf-v-slot`) | `-ns` namespace, `-bg` slotBackground, `-sc` slotColor, `-sp` slotPath |
| Link (`wpf-v-link`) | `-ns` namespace, `-lc` linkColor, `-lt` linkThickness |
| Tree (`wpf-v-tree`) | `-ns` namespace, `-bg` surfaceBackground, `-bb` surfaceBorderBrush, `-bt` surfaceBorderThickness |
| Selector (`wpf-v-selector`) | `-ns` namespace only |
| Decorator (`wpf-v-decorator`) | `-ns` namespace, `-bg` gridBackground, `-mic` minorGridColor, `-mac` majorGridColor, `-ac` axisColor, `-gs` gridSpacing, `-mle` majorLineEvery, `-rb` rulerBackground, `-rtc` rulerTickColor, `-rlc` rulerLabelColor, `-rdc` rulerDividerColor |
| Minimap (`wpf-v-minimap`) | `-ns` namespace, `-bg` minimapBackground, `-bdr` minimapBorder, `-nf` nodeFill, `-vs` viewportStroke |

**Note:** option short/long names are declared per package in each template's `.template.config/dotnetcli.host.json`, and they are **not guaranteed identical across suites** (e.g. the WinForms decorator long name for the background is `grid-background`, not `background`). The exact option list for any template is the one its own `.template.config/dotnetcli.host.json` declares; node/slot/link/tree/minimap templates ship extra template symbols (e.g. `nodeWidth` / `nodeHeight`) that are not surfaced as CLI options in the WPF host file.
