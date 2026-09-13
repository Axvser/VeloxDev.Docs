# AOP runtime — `ProxyMembers` & `ProxyHandler`

The hook contracts of the runtime. `ProxyMembers` selects which member kind a `ProxyEx.SetProxy` call registers against; `ProxyHandler` is the signature shared by the `start`, `coverage` and `end` hooks.

## Type: `ProxyMembers` (enum)

Declared in `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`:

```csharp
public enum ProxyMembers
{
    Getter,
    Setter,
    Method
}
```

Selects which hook table a registration writes to. Internally every `ProxyInstance` keeps three tables — `GetterActions`, `SetterActions`, `MethodActions` — keyed by the dispatched member name.

| Member | Hook table | Dispatched member-name key |
|---|---|---|
| `ProxyMembers.Getter` | `GetterActions` | `get_{Member}` (e.g. `get_Name`) |
| `ProxyMembers.Setter` | `SetterActions` | `set_{Member}` (e.g. `set_Name`) |
| `ProxyMembers.Method` | `MethodActions` | the bare method name (e.g. `Reset`) |

**Notes:** each table maps a key to a `Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>` — the `(start, coverage, end)` triple. A property is therefore intercepted through two independent registrations: one `Getter` entry under `get_*` and one `Setter` entry under `set_*`.

## Type: `ProxyHandler` (delegate)

Declared in `Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs`:

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

The shared signature for `start`, `coverage` and `end`.

### Invoke

**Signature:** `object? Invoke(object?[]? parameters, object? previous)`

| Parameter | Type | Description |
|---|---|---|
| `parameters` | `object?[]?` | The intercepted member's arguments, boxed. For a setter, `parameters[0]` is the value being written; for `AOP_OnMemberAdded`, `parameters[1]` is the `NotifyCollectionChangedEventArgs` |
| `previous` | `object?` | The result chained from the previous stage: `null` for `start`, the `start` result `R0` for `coverage`, the `coverage` / reflection result `R1` for `end` |

**Returns:** `object?` — only a non-null `coverage` handler's return value is honored as the member's result; `start` and `end` return values are currently discarded by the dispatcher.

**Exceptions:** none declared — a handler may throw, and the exception propagates out of `ProxyInstance.Invoke` to the proxy caller.

### The three-stage pipeline

For one proxied member call, the dispatcher — ProxyInstance.Invoke ([proxyinstance](../03_proxyinstance/index.md)) — runs:

```text
R0 = start?.Invoke(parameters, null)              // before the member body
R1 = coverage != null ? coverage.Invoke(parameters, R0)   // replaces the body
                     : reflect the real target member(parameters)
end?.Invoke(parameters, R1)                        // after the body
return R1
```

Demo-verified handlers, `Examples/AOP/WPF/Demo/MainWindow.xaml.cs` (`ConfigureAOP`):

```csharp
// start — runs before Name is read
p.SetProxy(ProxyMembers.Getter, nameof(TeamViewModel.Name),
    (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
    null,
    null);

// end — runs after Name is changed; parameters[0] is the new value
p.SetProxy(ProxyMembers.Setter, nameof(TeamViewModel.Name),
    null,
    null,
    (p, _) => { MessageBox.Show($"the name of team has been changed to {p?[0]}"); return null; });
```

Related pages: [ProxyEx](../02_proxyex/index.md) registers these hooks; [ProxyInstance](../03_proxyinstance/index.md) dispatches them.
