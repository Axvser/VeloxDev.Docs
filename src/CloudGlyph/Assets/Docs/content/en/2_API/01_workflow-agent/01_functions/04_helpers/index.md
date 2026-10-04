# Functions · Helper Classes

Three static helper classes back the command, patch and schema tools.

## CommandInvoker

`public static class CommandInvoker` — discovers and invokes `IVeloxCommand` properties on workflow components; backs `ListComponentCommands`, `ExecuteCommandOnNode`, `ExecuteCommandById`. Deserializes JSON parameters to the type declared by `[AgentCommandParameter]`.

| Member | Signature | Notes |
|---|---|---|
| `DiscoverCommands` | `IReadOnlyList<CommandDescriptor> DiscoverCommands(object component)` | `ICommand`-typed properties — interface properties first (authoritative attributes), then the concrete type's own (deduplicated). |
| `Invoke` | `string Invoke(object component, string commandName, string? jsonParameter)` | Executes a named command, returns JSON; the `"Command"` suffix is appended if missing. A missing command or a null command property returns a `status:"error"` JSON, not an exception. |

`CommandDescriptor` (`public class`) is declared in the same file: `Name` (`string`), `ParameterType` (`Type?`, from `[AgentCommandParameter]`), `Descriptions` (`IReadOnlyList<KeyValuePair<AgentLanguages, string>>`).

## ComponentPatcher

`public static class ComponentPatcher` — applies a JSON patch object to a component by setting writable public properties. Backs `PatchNodeProperties` / `PatchComponentById`.

| Member | Signature | Notes |
|---|---|---|
| `ApplyPatch` | `string ApplyPatch(object target, string jsonPatch)` | Applies `{"Prop": value}`. Rejects (with `rejected`/`skipped` + `reason`) framework-managed props (`Parent`, `Nodes`, `Links`, `LinksMap`, `Slots`, `Targets`, `Sources`, `State`, `VirtualLink`, `RuntimeId`, `Helper`), command-backed props (routed to their backing command), slot-typed and `[SlotSelectors]`-marked props; errors on a target not mounted in a tree; a `Type` property resolves names via `TypeIntrospector`. Direct writes are intentionally non-undoable. |
| `ApplyPatchWithUndo` | `string ApplyPatchWithUndo(object target, string jsonPatch, IWorkflowTreeViewModel? tree = null)` | Backward-compatible alias → `ApplyPatch` (`tree` ignored). |
| `CopyScalarProperties` | `void CopyScalarProperties(object source, object target)` | Copies writable scalar/enum properties, skipping command/slot/framework-managed ones. |

## TypeIntrospector

`public static class TypeIntrospector` — type resolution + JSON schema for Agent consumption; backs `GetTypeSchema`.

| Member | Signature | Notes |
|---|---|---|
| `ResolveType` | `Type? ResolveType(string fullTypeName)` | Delegates to `AgentTypeResolver.ResolveType` in Core. |
| `GetTypeSchema` | `string GetTypeSchema(Type type)` | Indented JSON: `fullName`, `kind` (enum/interface/struct/class), `baseType`, `interfaces`, enum `values` or property list (`name`/`type`/`canRead`/`canWrite`), plus developer instructions. |

## Example

```text
// Source: Test
CommandInvoker.DiscoverCommands(node)                 → [{Name:"ReceiveCommand", ParameterType:null, ...}]
CommandInvoker.Invoke(node, "ReceiveCommand", null)   → {"status":"ok","message":"Command 'ReceiveCommand' executed."}
CommandInvoker.Invoke(node, "NoSuchCommand", null)    → {"status":"error","message":"Command 'NoSuchCommandCommand' not found on type '...'."}
TypeIntrospector.ResolveType("System.String")         → typeof(string)
```

**Expected result:** an unknown command name is normalized to `NoSuchCommandCommand` and reported as an error, never thrown.
