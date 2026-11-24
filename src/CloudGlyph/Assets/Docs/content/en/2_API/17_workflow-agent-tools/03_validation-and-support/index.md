# Validation and support

These types back the `ValidateWorkflow`, `ExecuteCommandOnNode`, `PatchNodeProperties` and `GetTypeSchema` tools. They are usable directly, but most hosts only register a domain validator and let the toolkit call the rest.

## Interface: IWorkflowTreeValidator

`VeloxDev.AI.Workflow.IWorkflowTreeValidator` is a domain validator a host or plugin registers so `ValidateWorkflow` reports problems the structural lint cannot see. The toolkit owns the structural checks (zero-size nodes, duplicate links, cycles); a component library knows its own required fields and adds them here.

| Member | Signature | Description |
|---|---|---|
| `Name` | `string Name { get; }` | The name reported beside every issue this validator produces. |
| `Validate` | `IEnumerable<WorkflowValidationIssue> Validate(ITreeComponent tree)` | Returns the issues found. An empty sequence means the domain checks passed. The tree is live and must not be mutated. |

Implementations must be read-only. The registry is read once per `ValidateWorkflow` call, so a validator registered after the server starts is picked up next time.

## Record: WorkflowValidationIssue

```csharp
public sealed record WorkflowValidationIssue(
    string Level,
    int NodeIndex,
    string? ComponentId,
    string Message,
    string? Code = null);
```

| Parameter | Type | Description |
|---|---|---|
| `Level` | `string` | Severity: `error`, `warn` or `info`. |
| `NodeIndex` | `int` | The node the issue belongs to, or `-1` for a tree-level issue. |
| `ComponentId` | `string?` | The component's runtime id, when the issue belongs to one. |
| `Message` | `string` | A human-readable description. |
| `Code` | `string?` | An optional stable code the host can match on. |

## Class: WorkflowValidation

A process-wide registry of validators in `VeloxDev.AI.Workflow`.

| Method | Returns | Description |
|---|---|---|
| `Register(IWorkflowTreeValidator validator)` | `void` | Adds a validator; registering the same instance twice is a no-op. Throws `ArgumentNullException` when null. |
| `Unregister(IWorkflowTreeValidator validator)` | `bool` | Removes a validator; `true` when it was registered. |
| `Snapshot()` | `IReadOnlyList<IWorkflowTreeValidator>` | A stable copy of the registered validators. |
| `Clear()` | `void` | Removes every validator, for hosts and tests between sessions. |

Registration is normally done from an assembly's module initializer, so loading the assembly is what makes its validation available.

```csharp
using VeloxDev.AI.Workflow;

WorkflowValidation.Register(new MyDomainValidator());
var issues = new MyDomainValidator().Validate(tree);
```

## Class: CommandInvoker

`VeloxDev.AI.Workflow.Functions.CommandInvoker` discovers and invokes a component's command properties through its compiled context-tree entry. It is what `ListComponentCommands` and `ExecuteCommandOnNode` call.

| Method | Returns | Description |
|---|---|---|
| `DiscoverCommands(object component)` | `IReadOnlyList<CommandDescriptor>` | The command properties the tree records, including inherited ones; empty when the component is null or its type is not in the tree. |
| `Invoke(object component, string commandName, string? jsonParameter)` | `string` | Invokes a named command, deserializing the JSON parameter to the type `[AgentCommandParameter]` declared. A `Command` suffix is added when missing. Returns a JSON status object. |

`Invoke` does not consult the command's `CanExecute`; a command that reports it cannot run is still run.

## Class: CommandDescriptor

One command property a component exposes to the agent.

| Member | Type | Description |
|---|---|---|
| `Name` | `string` | The command property's name. |
| `ParameterType` | `Type?` | The type `[AgentCommandParameter]` declared, or `null` when the command takes no parameter. |
| `Descriptions` | `IReadOnlyList<KeyValuePair<AgentLanguages, string>>` | The command's descriptions, each with its language. |

## Class: ComponentPatcher

`VeloxDev.AI.Workflow.Functions.ComponentPatcher` applies a JSON patch object to a component by setting writable public properties. Properties backed by a command (e.g. `Anchor` → `SetAnchorCommand`) are rejected, so the command pipeline is not bypassed.

| Method | Returns | Description |
|---|---|---|
| `ApplyPatch(object target, string jsonPatch)` | `string` | Applies `{"Title":"New","Delay":500}`-style patches. Returns a JSON result describing successes and failures. |
| `ApplyPatchWithUndo(object target, string jsonPatch, ITreeComponent? tree = null)` | `string` | Backward-compatible alias; the tree argument is ignored and resolved from the target's parent chain. |
| `CopyScalarProperties(object source, object target)` | `void` | Copies writable, non-command, non-`ICommand` properties between two objects of the same type. |

## Class: TypeIntrospector

`VeloxDev.AI.Workflow.Functions.TypeIntrospector` describes a type the agent context tree carries, as JSON the model can read. Everything comes from the compiled context tree; no reflection is used.

| Method | Returns | Description |
|---|---|---|
| `ResolveType(string fullTypeName)` | `Type?` | Resolves a type by full name from the context tree; `null` when the tree carries none. |
| `GetTypeSchema(Type type)` | `string` | An indented JSON schema-like description: members, base type, interfaces and enum values. |

The schema is a description, not a contract. `defaultJson` is a zero-initialized instance rather than the author's intended defaults, so `developerInstructions` is the field a caller should trust.

## Related

- [WorkflowAgentToolkit](../01_workflow-agent-toolkit/index.md) — the tools that call these helpers.
- [WorkflowAgentScope](../00_workflow-agent-scope/index.md) — the scope owning the checked tree.
