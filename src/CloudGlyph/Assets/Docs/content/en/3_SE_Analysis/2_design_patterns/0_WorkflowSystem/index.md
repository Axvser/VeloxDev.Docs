# Design Patterns — WorkflowSystem

## 1. Builder Pattern (Source Generator)

The `[WorkflowBuilder.Tree<T>]`, `[WorkflowBuilder.Node<T>]`, `[WorkflowBuilder.Slot<T>]`, and `[WorkflowBuilder.Link<T>]` attributes are processed by the Roslyn source generator (`VeloxDev.Core.Generator`) to emit the full ViewModel implementation.

```csharp
// User writes:
[WorkflowBuilder.Tree<MyTreeHelper>]
public partial class MyTree { }

// Generator emits:
//   - Implement IWorkflowTreeViewModel
//   - InitializeWorkflow() method
//   - All required properties (Nodes, Links, Layout...)
//   - All required commands
//   - Serialization support
//   - Agent context metadata
```

**Why**: Reduces boilerplate dramatically. The user writes only the structure-specific logic (helpers). The repetitive property+command pattern is generated once by the analyzer.

## 2. Strategy Pattern (Helper System)

Each component type delegates its behavior to a **Helper** object:

```
Component        Helper
─────────       ──────
TreeViewModel  → TreeHelper<T>      : CreateLink, CreateNode, ValidateConnection
NodeViewModel  → NodeHelper<T>      : WorkAsync, ValidateBroadcastAsync
SlotViewModel  → SlotHelper<T>      : ValidateConnection
LinkViewModel  → LinkHelper<T>      : (lifecycle only)
```

The Helper is a pluggable strategy that can be replaced at runtime via `SetHelper()`. This separates the ViewModel's structural code (positions, collections) from its behavioral code (business logic, validation).

## 3. Mediator Pattern (Command-Based Communication)

Components do not call each other's methods directly. Instead, they communicate through a shared command interface (`IVeloxCommand`):

```
Node.MoveCommand.Execute(offset)  → Helper handles spatial update
Tree.SendConnectionCommand.Execute(slot) → Helper manages connection protocol
Slot.DeleteCommand.Execute(null)   → Helper removes links and notifies tree
```

This decouples the sender from the receiver. Commands can be intercepted, queued, logged, or undone via the `SubmitCommand`/`UndoCommand` mechanism.

## 4. Command Pattern (Undo/Redo)

Every mutating operation is wrapped in an `IWorkflowActionPair`:

```
User action → SubmitCommand(pair) → pair.Do()  → recorded in undo stack
User undo   → UndoCommand(null)   → pair.Undo() → moved to redo stack
User redo   → RedoCommand(null)   → pair.Do()  → moved back to undo stack
```

**Stack structure**: The tree maintains an undo stack and a redo stack. Actions can be batched for atomic undo/redo of compound operations.

## 5. Observer Pattern (Event-Driven Lifecycle)

Helpers subscribe to component events:

```
TreeHelper.NodeAdded    → Spatial manager indexes the node
TreeHelper.LinkAdded    → Spatial manager indexes the link pair
NodeHelper.WorkCommand  → Started / Completed / Failed / Exited events
```

The `HttpHelper<T>` example subscribes to `WorkCommand.Started`, `.Exited`, `.Enqueued`, `.Dequeued` to track runtime counters and display UI state.

## 6. Virtual Proxy Pattern (ViewPool + Virtualization)

The `ViewPool` attached behavior acts as a virtual proxy. Only items within the current `Viewport` are rendered:

```
IWorkflowTreeViewModelHelper.Viewport  → defines visible region
IWorkflowTreeViewModelHelper.VisibleItems → computed visible subset
ViewPool.ItemsSource = {Binding Helper.VisibleItems}  → only renders these
```

When the user pans/zooms, the viewport changes → `VisibleItems` recomputes → UI recycles views for off-screen items.

## 7. Spatial Hash Pattern (Grid-Based Indexing)

`SpatialGridHashMap<T>` uses a grid-based spatial hash for O(1) insertion/removal and efficient range queries:

```
Grid cell [x, y] → hashset of items in that cell
Insert: compute cell key → add to hashset (O(1))
Query: enumerate cells in viewport → collect items (O(cells_in_viewport))
Remove: compute cell key → remove from hashset (O(1))
```

Grid cell size is configurable. A larger cell size reduces memory but increases false positives during queries.

## 8. Layer/Anchor Pattern (Z-Index Management)

Each node has an `Anchor` with `Layer` (Z-index). When nodes overlap, the layer determines which node appears on top. The layer is automatically managed during creation and can be adjusted when nodes are moved.
