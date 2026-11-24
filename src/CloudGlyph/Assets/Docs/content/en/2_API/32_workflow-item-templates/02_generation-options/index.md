# Generation options

Every pack accepts the same option names and aliases, so a command line moves between GUIs unchanged. `template.json` declares each symbol and its default; `dotnetcli.host.json` supplies the aliases.

## The three structural options

| Option | Long name | Meaning |
| --- | --- | --- |
| `-n` | `--name` | Class name and file name. `sourceName` is `TemplateClass`, so it also rewrites `x:Class` and every reference. |
| `-ns` | `--namespace` | `TemplateNamespace` in every generated file. All seven must match. |
| `-o` | `--output` | Output folder. `preferNameDirectory` is `false`, so `-o Views` writes directly into `Views/` with no per-name subfolder. |

The built-in default class names are `TreeView`, `NodeView`, `SlotView`, `LinkView`, `TemplateSelector` (`CustomTemplateSelector` on WinForms), `GridDecorator` and `MinimapOverlay`. The namespace default is `MyApp.Views`.

## Style symbols

### Node view

| Short | Long | Symbol | Default |
| --- | --- | --- | --- |
| `-sb` | `surface-background` | `surfaceBackground` | `#FF1E1E1E` (WinForms only) |
| `-bg` | `background` | `nodeBackground` | `#DDFFFFFF` |
| `-fg` | `foreground` | `nodeForeground` | `#DD1E1E1E` |
| `-bb` | `border-brush` | `nodeBorderBrush` | `#331E1E1E` |
| `-bt` | `border-thickness` | `nodeBorderThickness` | `1` |
| `-cr` | `corner-radius` | `nodeCornerRadius` | `6` |

### Slot view

| Short | Long | Symbol | Default |
| --- | --- | --- | --- |
| `-bg` | `background` | `slotBackground` | `#01000000` |
| `-sp` | `slot-path` | `slotPath` | SVG path data (inert; see below) |
| `-sc` | `color` | `slotColor` | `#DD1E1E1E` |
| `-bc` | `border-color` | `slotBorderColor` | `#FFFFFFFF` |

### Link view

| Short | Long | Symbol | Default |
| --- | --- | --- | --- |
| `-lc` | `line-color` | `linkColor` | `#DDFFFFFF` |
| `-lt` | `line-thickness` | `linkThickness` | `2` |

### Tree view

| Short | Long | Symbol | Default |
| --- | --- | --- | --- |
| `-bg` | `background` | `surfaceBackground` | `#1E1E1E` |
| `-bb` | `border-brush` | `surfaceBorderBrush` | `#33FFFFFF` |
| `-bt` | `border-thickness` | `surfaceBorderThickness` | `1` |
| `-cr` | `corner-radius` | `surfaceCornerRadius` | `3` (WinForms `0`) |

### Grid decorator

| Short | Long | Symbol | Default |
| --- | --- | --- | --- |
| `-bg` | `background` | `gridBackground` | `#1E1E1E` |
| `-mic` | `minor-grid-color` | `minorGridColor` | `#2A2D2E` |
| `-mac` | `major-grid-color` | `majorGridColor` | `#3A3D40` |
| `-ac` | `axis-color` | `axisColor` | `#4D4D4D` |
| `-gs` | `grid-spacing` | `gridSpacing` | `40` |
| `-mle` | `major-line-every` | `majorLineEvery` | `5` |
| `-rb` | `ruler-background` | `rulerBackground` | `#C8252526` |
| `-rtc` | `ruler-tick-color` | `rulerTickColor` | `#555555` |
| `-rlc` | `ruler-label-color` | `rulerLabelColor` | `#888888` |
| `-rdc` | `ruler-divider-color` | `rulerDividerColor` | `#3A3D40` |

### Minimap overlay

| Short | Long | Symbol | Default |
| --- | --- | --- | --- |
| `-bg` | `background` | `minimapBackground` | `#331E1E1E` |
| `-bdr` | `border` | `minimapBorder` | `#DC94A3B8` |
| `-nf` | `node-fill` | `nodeFill` | `#DC38BDF8` |
| `-vs` | `viewport-stroke` | `viewportStroke` | `#F0FFFFFF` |

The selector item has no style symbols; only `-ns` applies.

## Inert symbols

A symbol with no consumer still parses and changes nothing. Those values exist for cross-GUI CLI parity and are documented in each pack's own `template.json`.

| GUI | Item | Inert symbol |
| --- | --- | --- |
| every pack | slot | `slotPath` — the glyph is an ellipse or a circle |
| Razor | slot | `slotBackground` |
| Razor | decorator | `gridBackground`, `minorGridColor`, `majorGridColor` |
| Razor | tree | `surfaceBorderBrush`, `surfaceBorderThickness`, `surfaceCornerRadius` |

When a colour refuses to appear, edit the generated file rather than the command line.

## Example

```powershell
dotnet new winforms-v-node -n NodeView -ns MyWorkflowApp.Views -o Views `
    -bg "#DD101820" -fg "#FFE5F4FF" -cr 10
```

**Expected result:** `Views/NodeView.xaml` and `Views/NodeView.xaml.cs` contain the new colours and corner radius. A symbol substitution also rewrites that value where it appears inside a generated comment; that is cosmetic.

### Notes

- Keep `-ns` identical across the seven commands; the tree resolves its siblings through it.
- The aliases are per item, not global: `-bg` means `nodeBackground` on the node item, `surfaceBackground` on the tree, and `minimapBackground` on the minimap.
