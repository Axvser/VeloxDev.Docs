# Workflow System — Key Member Contracts

Entry-template form for the headline top-level APIs.

### `WorkflowBuilder.TreeAttribute<T>`

**Signature:**

```csharp
[WorkflowBuilder.Tree<THelper>]
public partial class TreeViewModel { public TreeViewModel() => InitializeWorkflow(); }
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `virtualLinkType` | `Type?` | Optional override for the virtual-link type (default `LinkDefaultViewModel`) |
| `virtualSlotType` | `Type?` | Optional override for the slot type used inside the virtual link |

**Returns:** nothing (attribute applied to the `partial` class; the generator emits the members).

**Exceptions:** compilation error if `THelper` is not `IWorkflowTreeViewModelHelper, new()`.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, lines 11-13.

**Notes:** the attribute generic parameter is the tree's Helper; `InitializeWorkflow()` is generator-emitted.

### `IWorkflowTreeViewModelHelper.SendConnection` / `ReceiveConnection`

**Signature:**

```csharp
void SendConnection(IWorkflowSlotViewModel slot);
void ReceiveConnection(IWorkflowSlotViewModel slot);
```

**Parameters:** `slot` — the sender (or receiver) slot, attached to a node in the tree.

**Returns:** `void`.

**Exceptions:** none directly; a detached slot triggers `WorkflowGuard.Fail` in DEBUG builds.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, `Connect(tree, sender, receiver)` calls `tree.GetHelper().SendConnection(sender)` then `ReceiveConnection(receiver)`.

**Notes:** two-phase protocol; the link is created and the whole connection is submitted as one undoable `WorkflowActionPair`.

### `CompilerViewModel.CompileAsync`

**Signature:**

```csharp
Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component) where T : IWorkflowViewModel;
```

**Parameters:**

| Param | Type | Notes |
|---|---|---|
| `component` | `T : IWorkflowViewModel` | Must be an `IWorkflowNodeViewModel` (the start/controller node) |

**Returns:** `IReadOnlyList<CompiledGraph>` — one compiled graph per start; also populates `Graphs`.

**Exceptions:** `ArgumentException` if `component` is not an `IWorkflowNodeViewModel`.

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, lines 29-34 (`await Compiler.CompileAsync(this);`).

**Notes:** linear segments → `ExecuteEntry`, routers → `BranchEntry`, multi-target routes → `ParallelEntry`.

### `ComponentModelEx.Serialize` / `Deserialize`

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

**Example:** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, lines 185-193 (`this.Serialize()`); `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 46-51.

**Notes:** settings include `TypeNameHandling.Auto`, `PreserveReferencesHandling.Objects`, `WritablePropertiesOnlyResolver`.
