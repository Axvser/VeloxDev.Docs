# Workflow System — Key Member Contracts

Entry-template form for the headline top-level APIs.

## `WorkflowBuilder.TreeAttribute<T>`

**Signature:** `[WorkflowBuilder.Tree<T>(Type? virtualLinkType = default, Type? virtualSlotType = default)]` where `T : IWorkflowTreeViewModelHelper, new()` — declared in `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs` (the generic parameter is the tree's Helper).

**Real usage** — `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, line 14:

```csharp
[WorkflowBuilder.Tree<AgentHelper>]
public partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `virtualLinkType` | `Type?` | Optional override for the virtual-link type (default `LinkDefaultViewModel`) |
| `virtualSlotType` | `Type?` | Optional override for the slot type used inside the virtual link |

**Returns:** nothing (attribute applied to the `partial` class; the generator emits the members).

**Exceptions:** compilation error if `T` is not `IWorkflowTreeViewModelHelper, new()`.

**Notes:** the attribute's generic parameter is the tree's Helper (`AgentHelper : TreeHelper<TreeViewModel>(200)` in the demo); `InitializeWorkflow()` is generator-emitted.

## `IWorkflowTreeViewModelHelper.SendConnection` / `ReceiveConnection`

**Signature:**

```csharp
void SendConnection(IWorkflowSlotViewModel slot);
void ReceiveConnection(IWorkflowSlotViewModel slot);
```

**Parameters:** `slot` — the sender (or receiver) slot, attached to a node in the tree.

**Returns:** `void`.

**Exceptions:** none directly; a detached slot triggers `WorkflowGuard.Fail` in DEBUG builds.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, lines 268-272 — `Connect(tree, sender, receiver)` calls `tree.GetHelper().SendConnection(sender)` then `ReceiveConnection(receiver)`:

```csharp
private static void Connect(IWorkflowTreeViewModel tree, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)
{
    tree.GetHelper().SendConnection(sender);
    tree.GetHelper().ReceiveConnection(receiver);
}
```

**Notes:** two-phase protocol; the link is created and the whole connection is submitted as one undoable `WorkflowActionPair`.

## `CompilerViewModel.CompileAsync`

**Signature:**

```csharp
Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default)
    where T : IWorkflowViewModel;
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `component` | `T : IWorkflowViewModel` | Must be an `IWorkflowNodeViewModel` — the controller / entry (`Root`) or result terminal (`Terminal`) node |
| `role` | `CompileRole` | `Root` (forward compile of the reachable sub-graph) or `Terminal` (reverse-compile the node's ancestor cone; no explicit start required) |
| `ct` | `CancellationToken` | Optional cancellation |

**Returns:** `IReadOnlyList<CompiledGraph>` — one compiled graph for the request; also stored on `Graphs`.

**Exceptions:** `ArgumentException` if `component` is not an `IWorkflowNodeViewModel`; `ArgumentOutOfRangeException` for an unknown `role`; `InvalidOperationException` when a `Terminal` cone cannot be expressed (producers not funneling into one common join, or a router with several cone-reaching branches).

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, lines 33-34 (`await Compiler.CompileAsync(this, CompileRole.Root);`).

**Notes:** linear segments → `ChainSegment`; `ICompileTimeRouter` nodes → `BranchSegment` (static branches pruned by the compile-time key, dynamic kept all); multi-target routes or plain-node fan-out → `ParallelSegment`; no downstream → terminal branch. Execution is then driven by `RuntimeEngine.RunAsync(graph, context, ct)`.

## `ComponentModelEx.Serialize` / `Deserialize`

**Signature:**

```csharp
string Serialize<T>(this T workflow) where T : INotifyPropertyChanged;
T Deserialize<T>(this string json) where T : INotifyPropertyChanged;
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `workflow` | `T : INotifyPropertyChanged` | Any workflow tree ViewModel |
| `json` | `string` | JSON produced by `Serialize` (or an options variant) |

**Returns:** `Serialize` → JSON string; `Deserialize` → a new `T` instance.

**Exceptions:** `Serialize` → `ArgumentNullException` on null workflow; `Deserialize` → `ArgumentException` on null/empty JSON, `JsonSerializationException` when the result is null. `TryDeserialize` returns `false` instead of throwing.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, line 252 (`var json = this.Serialize();` in `SaveCommand`); `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 65-67 (`json.Deserialize<TreeViewModel>()` + `result.Layout.UpdateCommand.Execute(null)`).

**Notes:** settings include `TypeNameHandling.Auto`, `PreserveReferencesHandling.Objects`, `WritablePropertiesOnlyResolver`.
