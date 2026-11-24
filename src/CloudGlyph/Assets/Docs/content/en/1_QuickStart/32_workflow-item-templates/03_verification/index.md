# Verification and complete script

## The build is the check

Generation succeeding proves nothing: `dotnet new` substitutes strings without understanding them. The gate is:

```powershell
dotnet build
```

A generated suite is correct when it compiles against the adapter and the app shows the surface. The repository's own harness does the same mechanically: it packs, installs, generates all seven, compiles them together, and fails any file that still contains a `replaces` placeholder.

## Failures you will actually hit

| Symptom | Cause | Fix |
| --- | --- | --- |
| The tree cannot find its node view, or `CS0246` on a sibling type | the seven items went into different namespaces; a sibling was renamed; a sibling was not generated | one namespace, default names, all seven items |
| Avalonia: build fails at `x:DataType="vm:TreeViewModel"` | the pack ships a placeholder type that points at your ViewModels namespace | point `xmlns:vm` at your namespace and rename the type; the failure is intentional |
| A colour option changes nothing | the GUI has no consumer for that value | edit the generated file; check the inert-symbol table in [Customise](../02_customise/index.md) |
| The link menu opens with no Delete entry | the packs declare and wire the menu but add no entries | add the entry to the resource, fragment or `SetLinkMenuBuilder` call |
| Node text is squeezed and clips when zoomed out | the inner design grid was bound to the collapsed `Size` while the outer container already scales | pin the inner grid to `260 × 180`; let the container scale |
| Half of a port is hidden under the card | the port sits in a clipped container or under the card surface | give ports `ZIndex="6"` and keep clipping off on the card and its ancestors |
| A slot's visual state never changes | the view bound `Slot.State` instead of the slot's own `State` | set the slot control's `DataContext` to the slot and read `State` from it |
| Connecting or hovering stops after a view edit | `SlotView` was replaced by a plain shape, removing the gesture and the measurement | keep `SlotView`, or wrap `WorkflowSlotConnectionBehavior` exactly once |
| Ticks and nodes drift apart | the ruler value used for the canvas translation differs from `RulerBand` | read `RulerBand` and use it for translation, grid maths and virtualise inset |
| `dotnet new` resolves an older pack or install exits non-zero | duplicate registration, or a folder-mounted pack with the same short name | `dotnet new uninstall VeloxDev.<GUI>.Templates`, then install the NuGet pack |

## Complete script

Run from the project directory. It installs the pack and the adapter, generates the full suite with the defaults, and builds.

```powershell
dotnet new install VeloxDev.WinForms.Templates
dotnet add package VeloxDev.WinForms

dotnet new winforms-v-tree      -n TreeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-node      -n NodeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-slot      -n SlotView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-link      -n LinkView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-selector  -n CustomTemplateSelector -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views -o Views

dotnet build
```

For another GUI, swap `VeloxDev.WinForms.Templates` and `VeloxDev.WinForms` for the target pack and adapter, and swap the `winforms-v-` prefix. Keep the seven `-ns` values identical. On Razor every item produces a `.razor` + `.razor.cs` pair, so the suite is fourteen files.

Symbol sources:

- All 49 short names and the seven item identities — `Src/Templates/VeloxDev.<Platform>.Templates/working/content/workflow-<role>/.template.config/template.json`.
- The generated shapes — `Src/Templates/.../TemplateClass.*`, mirrored in `Examples/Workflow/<GUI> Trimmed/Demo/` (Razor: `Blazor Trimmed`).
- Pack metadata (`PackageType=Template`, `netstandard2.0`, version 12.0.0) — `Src/Templates/VeloxDev.<Platform>.Templates/working/VeloxDev.<Platform>.Templates.csproj`.

## Run declaration

⚠️ Not actually run — statically verified against `Src/Templates/` on 2026-11-25. The 49 short names and the identities were read from every `template.json`; the script itself was not executed here, so no build output is recorded.
