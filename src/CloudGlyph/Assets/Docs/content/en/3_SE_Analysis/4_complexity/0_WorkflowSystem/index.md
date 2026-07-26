# Complexity Analysis — WorkflowSystem

## Class Hierarchy Complexity

```
IWorkflowViewModel (base)
├── IWorkflowTreeViewModel    ← 10 properties, 8 commands
├── IWorkflowNodeViewModel    ← 5 properties, 9 commands
├── IWorkflowSlotViewModel    ← 6 properties, 5 commands
└── IWorkflowLinkViewModel    ← 4 properties

Helper Hierarchy:
IWorkflowHelper (base)
├── IWorkflowTreeViewModelHelper  ← +events, Install/Uninstall, CreateNode/Link
├── IWorkflowNodeViewModelHelper  ← +events, WorkAsync, ValidateBroadcastAsync
├── IWorkflowSlotViewModelHelper  ← +events
└── IWorkflowLinkViewModelHelper  ← +events

Implementation Hierarchy:
TreeHelper<T>         → IWorkflowTreeViewModelHelper  (default: ~200 lines)
NodeHelper<T>         → IWorkflowNodeViewModelHelper  (default: ~80 lines)
SlotHelper<T>         → IWorkflowSlotViewModelHelper  (default: ~50 lines)
LinkHelper<T>         → IWorkflowLinkViewModelHelper  (default: ~30 lines)
```

## Spatial Grid Complexity

| Operation | Time | Space | Notes |
|---|---|---|---|
| `Insert` | O(1) | O(n) | Hash-based cell insertion |
| `Remove` | O(1) | O(1) | Hash-based cell removal |
| `Query` | O(k + m) | O(1) | k = cells in viewport, m = items in range |
| `Update` | O(2) | O(1) | Remove + reinsert |
| `Global Bounds` | O(1) | O(1) | Maintained incrementally |

- **Grid cell size**: Configurable (default 200px). Smaller cells = fewer false positives but more memory.
- **Worst case**: All items in one cell → query degrades to O(n).

## Workflow Compilation Complexity

The `WorkflowCompiler` builds a directed execution graph from the node/link structure:

```
Input: N nodes, L links
Step 1: Topological sort → O(N + L)
Step 2: Component analysis → O(N + L) (handles disconnected subgraphs)
Step 3: Cycle detection → O(N + L) (Tarjan's or DFS-based)
Step 4: Execution plan generation → O(N + L)

Total: O(N + L) time, O(N + L) space
```

**Cycle handling strategies**:
- `Error`: Fail compilation with cycle error
- `SkipCyclic`: Execute acyclic subset only
- `Ordered`: Fallback to insertion order

## Code Size Statistics (Approximate)

| Component | Source Files | Lines of Code |
|---|---|---|
| Core interfaces | 12 | ~600 |
| Core implementation (`WorkflowSystem/`) | 30 | ~3,500 |
| Templates/ViewModels | 6 | ~1,200 |
| Compilation pipeline | 15 | ~2,500 |
| Spatial indexing | 4 | ~500 |
| Selector extensions | 4 | ~400 |
| Standard extensions | 6 | ~800 |
| Tests | 8 | ~4,000+ |
| **Subtotal (WorkflowSystem)** | **~85** | **~13,500** |

## Dependency Graph Complexity

```
External deps: None (core is dependency-free)
Internal deps:
  VeloxDev.Core (self)
  └── VeloxDev.Core.Generator (source gen, compile-time only)

Adapter deps:
  VeloxDev.WorkflowSystem (core)
  └── VeloxDev.WPF / Avalonia / WinUI / MAUI (attached behaviors + platform adapters)
```

The core workflow system has **zero external NuGet dependencies**, making it lightweight and portable across all target frameworks.
