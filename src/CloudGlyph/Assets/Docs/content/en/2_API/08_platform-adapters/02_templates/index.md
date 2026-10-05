# API — Workflow View Templates

Each adapter ships a `dotnet new` item-template suite (`VeloxDev.{Platform}.Templates`, source under `Src/Templates/VeloxDev.*.Templates`) that scaffolds the workflow views with the behaviors already connected. Templates are installed with the standard `dotnet new install` and used with `dotnet new <shortName> -n <ClassName>`.

## Template suite per adapter

All suites contain the same seven kinds: node view, slot view, link view, tree view, template selector, grid decorator, minimap overlay. Short names are `{prefix}-v-{kind}` on every platform (grid decorator = `{prefix}-v-decorator`).

| Package | Node | Slot | Link | Tree | Selector | Decorator | Minimap |
|---|---|---|---|---|---|---|---|
| `VeloxDev.WPF.Templates` | `wpf-v-node` | `wpf-v-slot` | `wpf-v-link` | `wpf-v-tree` | `wpf-v-selector` | `wpf-v-decorator` | `wpf-v-minimap` |
| `VeloxDev.Avalonia.Templates` | `ava-v-node` | `ava-v-slot` | `ava-v-link` | `ava-v-tree` | `ava-v-selector` | `ava-v-decorator` | `ava-v-minimap` |
| `VeloxDev.WinUI.Templates` | `winui-v-node` | `winui-v-slot` | `winui-v-link` | `winui-v-tree` | `winui-v-selector` | `winui-v-decorator` | `winui-v-minimap` |
| `VeloxDev.MAUI.Templates` | `maui-v-node` | `maui-v-slot` | `maui-v-link` | `maui-v-tree` | `maui-v-selector` | `maui-v-decorator` | `maui-v-minimap` |
| `VeloxDev.WinForms.Templates` | `winforms-v-node` | `winforms-v-slot` | `winforms-v-link` | `winforms-v-tree` | `winforms-v-selector` | `winforms-v-decorator` | `winforms-v-minimap` |
| `VeloxDev.Razor.Templates` | `razor-v-node` | `razor-v-slot` | `razor-v-link` | `razor-v-tree` | `razor-v-selector` | `razor-v-decorator` | `razor-v-minimap` |
| `VeloxDev.Jalium.Templates` | `jalium-v-node` | `jalium-v-slot` | `jalium-v-link` | `jalium-v-tree` | `jalium-v-selector` | `jalium-v-decorator` | `jalium-v-minimap` |

## Default names & generated files

Each template's default class name is `NodeView`, `SlotView`, `LinkView`, `TreeView`, `TemplateSelector`, `GridDecorator`, or `MinimapOverlay` respectively (set the actual name with `-n <Name>`). The node/slot/link/tree templates generate a markup + code-behind pair on the XAML-style platforms (`.xaml`/`.cs` or Avalonia/WinUI equivalents), while selector/decorator/minimap generate a single code-behind file. Razor generates `.razor` (+ `.razor.cs`) files.

## The seven pieces come pre-connected

A generated project needs no hand-wiring. The **tree view** is the hub: it hosts the pool and the surface behaviors and references its sibling templates — the node/slot/link views by name, and the **template selector** as the thing the pool asks first.

| Adapter | How the tree view hands the selector to the pool |
|---|---|
| WPF / Avalonia / WinUI / MAUI | `ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}"` — an attached property on the canvas |
| WinForms | `ViewPool.SetTemplateSelector(PART_Canvas, _selector)` — this platform has no attached-property system, so the pool is fed with a method call |
| Jalium | `ViewPool.SetTemplateSelector(this, TemplateSelector)`; the selector property ships with a **default value**, so a generated tree view is never selector-less |
| Razor | a `<TemplateSelector …>` component whose `ItemTemplate` is the pool's only source of views |

**The selector is the highest-priority source of views**, and it is asked *before* the platform's own template lookup; on the adapters that have such a lookup (the four XAML-style ones) a non-matching selector degrades to it, while WinForms/Jalium/Razor have nothing to degrade to — a missing selector there yields no views and no error (see [View pool](../00_attached-behaviors/01_view-pool/index.md)). To customize, replace the generated selector class or that single reference — not the pool.

## The link context menu

The tree-view template also declares the **link context menu** and points the surface at it. The wiring (right press, positioning, open/close, hub reporting) belongs to the adapter, not to the template code-behind — the XAML four add one attached property plus the menu resource, Razor passes a fragment parameter, and the code-only two override a hook:

| Adapter | Declaration |
|---|---|
| WPF / Avalonia | a `ContextMenu` resource keyed by `WorkflowSurfaceBehavior.LinkMenuKey` |
| WinUI / MAUI | a `MenuFlyout` resource keyed the same way |
| Razor | a `<LinkMenu Context="link">…</LinkMenu>` fragment parameter on the surface component |
| WinForms / Jalium | `WorkflowTreeView.OnBuildLinkMenu(menu, link)` — the base adds a single "Delete" item |

Each entry binds the link it acts on, so adding or removing an action is a template-only edit: a `MenuItem` / `MenuFlyoutItem` with `Command="{Binding DeleteCommand}"`, or a Razor button with `@onclick="() => link.DeleteCommand.Execute(null)"`. The Avalonia menu resource carries no `x:DataType`, so under compiled bindings it writes `{ReflectionBinding DeleteCommand}`.

On Razor, that `@onclick` only binds because the library ships an `_Imports.razor` containing `@using Microsoft.AspNetCore.Components.Web` (`Src/Adapters/VeloxDev.Razor/_Imports.razor`). The file is load-bearing, not cosmetic: without it the compiler emits the handler as a **literal attribute** (`"@onclick"`) and it never runs. A consuming project that compiles the generated Razor views needs the same import.

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
