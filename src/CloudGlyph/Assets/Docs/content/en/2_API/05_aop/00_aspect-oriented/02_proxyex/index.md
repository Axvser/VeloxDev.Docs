# AOP runtime — `ProxyEx` (static)

`Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`. It declares `ProxyMembers` and the single public registration method, `SetProxy`. There is no `CreateProxy`: the proxy is a generated class, constructed by the generated `Aop()` extension.

## ProxyEx.SetProxy\<T\>

**Signature:**

```csharp
public static void SetProxy<T>(
    this T target,
    ProxyMembers memberType,
    string memberName,
    ProxyHandler? start,
    ProxyHandler? coverage,
    ProxyHandler? end)
    where T : IAspectOriented
```

| Parameter | Type | Description |
|---|---|---|
| `target` | `T` | The proxy returned by `Aop()`. Passing the original object is rejected. |
| `memberType` | `ProxyMembers` | `Getter`, `Setter`, or `Method` — builds the interception key |
| `memberName` | `string` | The member's plain name, e.g. `nameof(TeamViewModel.Name)` |
| `start` | `ProxyHandler?` | Runs before the member, or `null` |
| `coverage` | `ProxyHandler?` | Replaces the member when non-null, or `null` |
| `end` | `ProxyHandler?` | Runs after the member, or `null` |

**Returns:** `void`

**Exceptions:**

| Exception | Condition |
|---|---|
| `InvalidOperationException` | `target` is not an `IAopHookTarget`, i.e. it is not a generated proxy |
| `ArgumentOutOfRangeException` | The built key matches no interceptable member of the proxied type |

### Behavior

1. Rejects a non-proxy target. The check matters because `IAspectOriented` is an empty marker anyone can implement; aspects installed on a hand-written implementation would never run.
2. Builds the key: `"get_" + memberName`, `"set_" + memberName`, or `memberName`.
3. Calls `IAopHookTarget.SetHooks(key, new AspectHooks(start, coverage, end))`.

Passing a `null` set is impossible through this method — the three arguments always produce an `AspectHooks` instance. An all-null set (`null, null, null`) runs the member's body with no hooks, but the member's slot stays non-null, so it keeps taking the hooked path; only `IAopHookTarget.SetHooks(key, null)` clears a slot.

Installing twice on the same member **replaces** the previous set; there is no stacking.

Demo usage, `Examples/AOP/WPF/Demo/MainWindow.xaml.cs` (`ConfigureAOP`):

```csharp
var p = data.Aop();

p.SetProxy(ProxyMembers.Getter,
    nameof(TeamViewModel.Name),
    (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
    null,
    null);

p.SetProxy(ProxyMembers.Method,
    nameof(TeamViewModel.Reset),
    null,
    (_, _) => { MessageBox.Show($"the default Reset() has been cancelled"); return null; },
    null);
```

**Notes:**

- `target` must be the object `Aop()` returned. Compile-time protection exists only for the user class: it does not implement `IAspectOriented`, so `counter.SetProxy(...)` on the raw target does not satisfy the constraint. A hand-written implementation still compiles and is rejected at runtime.
- Registration is unaffected by thread affinity; the generated proxy stores one field per member.

Related pages: [hook contracts](../01_proxy-members-handler/index.md) describe the delegate and set; [Generated proxy](../03_proxy-class/index.md) consumes them; [Aop & AopCache](../04_proxy-lifecycle/index.md) supplies the proxy.
