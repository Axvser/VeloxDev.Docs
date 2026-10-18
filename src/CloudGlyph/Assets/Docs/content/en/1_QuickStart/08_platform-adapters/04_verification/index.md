# Platform Adapters — Verification

## 1. Observable results to check

Host the generated views (Setup + Core Usage) and confirm each behavior:

| Action | Observable result |
|---|---|
| Drag the blank background | The surface pans; grid/ruler and minimap track the scroll offsets. |
| Ctrl + mouse-wheel over the surface | Zoom around the viewport center; the viewport indicator in the minimap updates. |
| Drag a node header | The node moves with the cursor; its input/output slot anchors follow. |
| Press an output slot, move the pointer over an input slot, then release | While moving, the candidate slot shows `PreviewReceiver` and the virtual link reports `ValidTarget` (or `InvalidTarget` for a slot Core would refuse); releasing over a valid slot creates the link; slot pins recolor by `SlotState`. |
| Scroll far / add many nodes | Only the visible item views are realized (virtualization) — the visible-items counter stays bounded. |
| Drag inside the minimap | The surface scrolls to the minimap position. |

## 2. Run the in-repo demo

The richest reference implementation is the WPF demo:

```powershell
dotnet run --project Examples/Workflow/WPF/Demo
```

Open the workflow tree on the left panel ("Load Workflow Demo"), then compare the **节点总数** (total nodes) counter with the **可见组件数** (visible components) counter: the latter stays small however large the tree becomes, which confirms `ViewPool` virtualization. Every platform has an equivalent demo under `Examples/Workflow/<Platform>` (each with a `Trimmed` variant), and Transition/Theme demos under `Examples/Transition/*` and `Examples/Theme/*` show the adapter transition/theme wiring.

## Run declaration

- ⚠️ **Not built or run for this revision (2026-10-18).** Every claim on this page is statically verified against the adapter source (`Src/Adapters/*`), the Core input/preview path (`Src/Core/VeloxDev.Core/WorkflowSystem`), and the demo call shapes (`Examples/Workflow/WPF/Demo`, `Examples/Transition/WPF`, `Examples/Theme/WPF`). No GUI was launched, so pan / zoom / drag / connect-preview / minimap were not observed on screen.
- ✅ Historical record (2026-10-01, not re-run): `dotnet build Examples/Workflow/WPF/Demo/Demo.csproj` (Debug, `net9.0-windows`) compiled the WPF adapter and its workflow behaviors against the Core engine with **0 warnings / 0 errors**:

```text
  VeloxDev.WPF -> ...\Src\Adapters\VeloxDev.WPF\bin\Debug\net5.0-windows\VeloxDev.WPF.dll
  Demo -> ...\Examples\Workflow\WPF\Demo\bin\Debug\net9.0-windows\Demo.dll

已成功生成。
    0 个警告
    0 个错误
```
