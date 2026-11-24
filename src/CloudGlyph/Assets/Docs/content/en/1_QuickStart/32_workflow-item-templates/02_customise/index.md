# Customise the generated views

The generated files are defaults, not fixtures. Edit them for your node types, your menu and your selection rules.

## Style parameters

Every pack accepts the same option names and aliases, so a command line moves between GUIs unchanged. The aliases live in each item's `.template.config/dotnetcli.host.json`; `template.json` declares the symbol and its default. A `template.json` symbol without `replaces` is accepted by the CLI and changes nothing; the packs keep a few deliberately empty symbols for cross-GUI CLI parity and say so in their own `template.json` (see the inert-value table below).

| Item | Option (short → symbol) | Meaning |
| --- | --- | --- |
| node | `-bg` `nodeBackground` | card fill |
| node | `-fg` `nodeForeground` | card text and glyph colour |
| node | `-bb` `nodeBorderBrush` | card border |
| node | `-bt` `nodeBorderThickness` | card border width |
| node | `-cr` `nodeCornerRadius` | card corner radius |
| slot | `-sc` `slotColor` | glyph fill |
| slot | `-bc` `slotBorderColor` | glyph outline |
| link | `-lc` `linkColor` | settled link stroke |
| link | `-lt` `linkThickness` | settled link width |
| tree | `-bg` `surfaceBackground` | surface fill |
| tree | `-bb` `surfaceBorderBrush` | surface border |
| tree | `-bt` `surfaceBorderThickness` | surface border width |
| tree | `-cr` `surfaceCornerRadius` | surface corner radius |
| decorator | `-gs` `gridSpacing` | spacing between grid lines |
| decorator | `-mle` `majorLineEvery` | minor lines per major line |
| decorator | `-rb` `rulerBackground` | ruler band fill |
| decorator | `-rtc` `rulerTickColor` | ruler tick |
| decorator | `-rlc` `rulerLabelColor` | ruler label |
| minimap | `-bg` `minimapBackground` | thumbnail background |
| minimap | `-nf` `nodeFill` | node mark fill |
| minimap | `-vs` `viewportStroke` | viewport indicator stroke |

A colour symbol can still have no consumer on a given GUI. Those packs declare the symbol for cross-GUI CLI parity and say so in their own `template.json`; the command line stays uniform, and the generated file documents the inert value. Known inert values:

| GUI | Item | Inert symbol |
| --- | --- | --- |
| every pack | slot | `slotPath` — the glyph is an ellipse or a circle |
| Razor | slot | `slotBackground` |
| Razor | decorator | `gridBackground`, `minorGridColor`, `majorGridColor` |
| Razor | tree | `surfaceBorderBrush`, `surfaceBorderThickness`, `surfaceCornerRadius` |

When a colour refuses to appear, edit the generated file directly rather than the command line. A symbol substitution also rewrites that value where it appears inside a generated comment; that is cosmetic.

## The selector

The VeloxDev selector (`ViewPool.TemplateSelector` / `ViewSourcePipeline`) has the highest priority: a match wins, and the platform's own template lookup is the fallback.

- WinForms derives `Easel.Visuals.VisualTemplateSelector` and returns visual `NodeView` / `SlotView` / `LinkView` instances. The pool has no platform fallback there, so the selector is the only creation path.
- Jalium derives `DataTemplateSelector`; its default selector leaves `SlotTemplate` and `TreeTemplate` unset, and those item kinds do not enter the pool.
- Razor's "selector" is a component (`TemplateSelector`) wrapping `ViewPool`; there is no selector instance.

The generated tree already wires the selector resource. The selector decides which view a ViewModel gets; keep that decision in the selector rather than branching inside the tree.

## The link menu

The tree declares the menu and wires the right-press. It ships **empty** — a right-press opens a menu with no Delete entry until you add one.

| GUI | Where the entries go |
| --- | --- |
| WPF / Avalonia / WinUI / MAUI / Jalium | a resource (`ContextMenu` / `MenuFlyout`) named by `WorkflowSurfaceBehavior.LinkMenuKey`; each entry is `Command="{Binding DeleteCommand}"` |
| WinForms | the tree's `VisualContextMenu x:Key="LinkContextMenu"`, or the host's `WorkflowSurfaceBehavior.SetLinkMenuBuilder(this, …)` |
| Razor | the `<LinkMenu Context="link">` fragment in the tree; each entry is an inline `@onclick` |

Each entry receives the right-pressed link, so one line is a complete action. The menu is positioned by the adapter, which also suspends input routing while it is open.

## Node content and ports

- Put your content on the design-size grid (`260 × 180` on the XAML platforms, WinForms and Jalium; a CSS transform on Razor). The container handles zoom; do not bind the inner grid to the collapsed `Size`.
- A port the card shows must be named. Rename a `PART_*` in the markup and in the slot-layout attribute together; nothing enumerates `node.Slots`.
- Keep the wrappers: `WorkflowSlotLayoutBehavior` outside and `WorkflowNodeDragBehavior` on the title strip. On Razor, `SlotView` already opens `WorkflowSlotConnectionBehavior` — wrapping it twice doubles both the measurement and the gesture.
- Slot colours are fixed template colours. `ISlotComponent.State` is not read by the template; subscribe to `PropertyChanged` in the host if you want state-driven appearance.

## Cross-pack differences that break a copy

- **Link strategy.** MAUI draws every link in one viewport-level overlay; WinForms and the XAML packs instantiate one link view per link. Copying a link view across that boundary produces a build that passes and a canvas with no links.
- **Ruler thickness.** The packs default to 28, except Jalium at 36. Read `RulerBand` from the decorator and use the same value for the canvas translation, the grid maths and the virtualise inset.
- **Avalonia's placeholder type.** `vm:TreeViewModel` in the generated tree is your type, not a generated one. The build failure until you repoint it is intentional: a clear error beats a canvas that silently renders nothing.
- **The debug HUD is not in any pack.** The demos carry an `InfoOverlay`; add your own if you want it.

**Expected result:** after a style edit, `dotnet new` produces the new value in the generated file; after a menu or selector edit, the rebuilt app shows the new behaviour.
