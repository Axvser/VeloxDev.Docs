# Platform Adapters — Verification

## 1. Observable results to check

Host the generated views (Setup + Core Usage) and confirm each behavior:

| Action | Observable result |
|---|---|
| Drag the blank background | The surface pans; grid/ruler and minimap track the scroll offsets. |
| Ctrl + mouse-wheel over the surface | Zoom around the viewport center; the viewport indicator in the minimap updates. |
| Drag a node header | The node moves with the cursor; its input/output slot anchors follow. |
| Press an output slot, release over an input slot | A link is created; slot pins recolor by `SlotState`. |
| Scroll far / add many nodes | Only the visible item views are realized (virtualization) — the visible-items counter stays bounded. |
| Drag inside the minimap | The surface scrolls to the minimap position. |

## 2. Run the in-repo demo

The richest reference implementation is the WPF demo:

```powershell
dotnet run --project Examples/Workflow/WPF/Demo
```

Open the workflow tree on the left panel ("Load Workflow Demo"), then compare the **节点总数** (total nodes) counter with the **可见组件数** (visible components) counter: the latter stays small however large the tree becomes, which confirms `ViewPool` virtualization. Every platform has an equivalent demo under `Examples/Workflow/<Platform>` (each with a `Trimmed` variant), and Transition/Theme demos under `Examples/Transition/*` and `Examples/Theme/*` show the adapter transition/theme wiring.

## Run declaration

- ✅ Built on 2026-10-01: `dotnet build Examples/Workflow/WPF/Demo/Demo.csproj` (Debug, `net9.0-windows`) compiled the WPF adapter and its workflow behaviors against the Core engine from this repository with **0 warnings / 0 errors**:

```text
  VeloxDev.WPF -> ...\Src\Adapters\VeloxDev.WPF\bin\Debug\net5.0-windows\VeloxDev.WPF.dll
  Demo -> ...\Examples\Workflow\WPF\Demo\bin\Debug\net9.0-windows\Demo.dll

已成功生成。
    0 个警告
    0 个错误
```

- ⚠️ Not launched: no GUI was started in this environment, so the interactive results in section 1 (pan / zoom / drag / connect / minimap) are statically verified against the adapter source (`Src/Adapters/*`) and the demo call shapes (`Examples/Workflow/WPF/Demo`, `Examples/Transition/WPF`, `Examples/Theme/WPF`) — they were not observed on screen.
