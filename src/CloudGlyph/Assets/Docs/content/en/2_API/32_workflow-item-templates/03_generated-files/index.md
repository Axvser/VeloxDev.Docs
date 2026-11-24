# Generated files

This page lists what each role emits and which behaviours are already wired. Edit the generated files for your node types, menu and selection rules; they are defaults, not fixtures.

## File shapes

| Pack | Markup extension | Pair roles | Standalone roles | Files per suite |
| --- | --- | --- | --- | --- |
| WPF | `.xaml` + `.xaml.cs` | tree, node, slot, link | selector, decorator, minimap | 11 |
| Avalonia | `.axaml` + `.axaml.cs` | tree, node, slot, link | selector, decorator, minimap | 11 |
| WinUI | `.xaml` + `.xaml.cs` | tree, node, slot, link | selector, decorator, minimap | 11 |
| MAUI | `.xaml` + `.xaml.cs` | tree, node, slot, link | selector, decorator, minimap | 11 |
| WinForms | `.xaml` + `.xaml.cs` | tree, node, slot, link | selector, decorator, minimap | 11 |
| Jalium | `.jalxaml` + `.jalxaml.cs` | tree, node, slot, link | selector, decorator, minimap | 11 |
| Razor | `.razor` + `.razor.cs` | tree, node, slot, link, selector, decorator, minimap | — | 14 |

The content file is always named `TemplateClass.*` before substitution; `-n` renames both the file and the class.

## What each role wires

| Role | Generated content |
| --- | --- |
| tree | Surface parts (`PART_Canvas`, `PART_ScrollViewer`, `PART_GridDecorator`, `PART_SurfaceBorder`, `PART_MinimapOverlay`), the templates for node/link, the selector resource, the empty link menu, and the surface attached properties or component parameters. |
| node | Design-size card, title strip with node drag, named slot parts with slot layout, and the port wrappers. |
| slot | Slot glyph with the slot-connection behaviour; on Razor it also opens the slot-layout and connection components. |
| link | One link view per link. The XAML packs publish the curve for hit testing; Jalium additionally calls `WorkflowLinkBounds.Apply` before drawing. |
| selector | `ViewPool.TemplateSelector` / `ViewSourcePipeline` dispatch. WinForms derives `Easel.Visuals.VisualTemplateSelector`; Jalium derives `DataTemplateSelector`; Razor's selector is a component wrapping `ViewPool`. |
| decorator | Grid and ruler drawing implementing `IWorkflowGridDecorator`; default ruler thickness 28, Jalium 36. |
| minimap | Thumbnail and viewport block implementing `IWorkflowMinimapOverlay`; drag-to-pan where the platform supports it. |

## The link menu ships empty

The tree declares the menu and wires the right-press, but adds no entries.

| GUI | Where entries go |
| --- | --- |
| WPF / Avalonia / WinUI / MAUI / Jalium | a resource (`ContextMenu` / `MenuFlyout`) named by `WorkflowSurfaceBehavior.LinkMenuKey`; `Command="{Binding DeleteCommand}"` |
| WinForms | the tree's `VisualContextMenu x:Key="LinkContextMenu"`, or the host's `SetLinkMenuBuilder(this, …)` |
| Razor | the `<LinkMenu Context="link">` fragment; each entry is an inline `@onclick` |

Each entry receives the right-pressed link, so one line is a complete action.

## Platform differences that break a copy

- **Link strategy.** MAUI draws every link in one viewport-level overlay; WinForms and the XAML packs instantiate one link view per link. Copying a link view across that boundary produces a build that passes and a canvas with no links.
- **Ruler thickness.** Packs default to 28, except Jalium at 36. Read `RulerBand` from the decorator and use the same value for the canvas translation, grid maths and virtualize inset.
- **Avalonia's placeholder type.** `vm:TreeViewModel` is your type, not a generated one. The build failure until you repoint it is intentional.
- **Jalium's transform mirror.** The tree class must re-expose `CanvasTransform`; without it every card stays at the world origin after a pan.
- **The debug HUD is not in any pack.** The demos carry an `InfoOverlay`; add your own if you want it.

## The build is the check

`dotnet new` substitutes strings without understanding them; generation success proves nothing.

```powershell
dotnet new winforms-v-tree -n TreeView -ns MyWorkflowApp.Views -o Views
# … the other six roles, same -ns …
dotnet build
```

**Expected result:** `dotnet build` exits `0` and the app shows the surface. A generated suite is correct only when it compiles against the adapter and runs.

### Notes

- The repository's `* Trimmed` demos are minimal-call-sequence mirrors of these roles, not publish-trim or AOT validation.
- A partial suite fails with `CS0246` because the tree type-references its siblings.
- If a colour option changes nothing, edit the generated file; see the inert-symbol table in [Generation options](../02_generation-options/index.md).
