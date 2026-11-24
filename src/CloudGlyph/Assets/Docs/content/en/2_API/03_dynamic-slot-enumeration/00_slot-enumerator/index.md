# Slot enumerator

`SlotEnumerator<TSlot>` owns one `ConditionalSlot<TSlot>` per selector value and exposes the selector as a bindable `CurrentValue`. Installing it registers it with the owning node, so a caller holding only the node can still reach the ports.

Namespace: `VeloxDev.WorkflowSystem`.

**Signature:** `partial class SlotEnumerator<TSlot> : IConditionalSlotProvider<TSlot>, IConditionalSlotProvider, INotifyPropertyChanged where TSlot : ISlotComponent, new()`

## Properties

| Member | Type | Description |
| --- | --- | --- |
| `Parent` | `INodeComponent?` | The node the enumerator is installed on; null while detached. |
| `SelectorTypeName` | `string` | The selector type's stored name; the serialization key. |
| `SelectorType` | `Type?` | The resolved selector type; protected setter. |
| `Items` | `ObservableCollection<ConditionalSlot<TSlot>>` | One entry per selector value. |
| `Count` | `int` | `Items.Count`, after flushing deferred removals. |
| `this[int index]` | `TSlot` | The slot of the entry at `index`. |
| `CurrentValue` | `object?` | Selected value. The setter normalises it onto the selector type and records it per selector type; the getter returns the value as text. |
| `ConditionMap` | (private) | `object` selector value → `TSlot`; not public. |

`CurrentValue` never records a null: a transient null from a regenerated items source does not become the remembered selection.

## Methods

### SetSelector

**Signature:** `void SetSelector(object? selector)`

Builds a new port set from `selector`:

| Selector argument | Ports |
| --- | --- |
| `Type` that is an enum | One branch per `Enum.GetNames` member, in value order. |
| `Type` that is `bool` | Two branches: `false`, `true`. |
| Fully-qualified type-name `string` | Resolved with `Type.GetType`, then treated as above. |
| `ISlotProvider` instance | One branch per `GetSlots()` definition; `Value` is the routing key, `Label` the display name. |

Before replacing the set it captures each current branch's wiring in both directions. On a fresh selector type, each new branch is re-connected to the neighbours of the old branch it stands for:

- between two **enum types**, identity is the **position**;
- for the **same provider type**, identity is the **name**, so reordering a port list never moves a connection.

Each selector type's full state is remembered, so switching back restores its branches, wiring and selection. The whole switch is one `ActionPair` on the tree; on a detached node the state is applied directly with no undo entry. A missing parent node, or a selector that cannot be resolved to a type, fails through `WorkflowGuard.Fail`/`Debug.Fail` rather than throwing.

Calling it with the currently installed enum type returns immediately (`SelectorTypeName` equality).

### TrySelect

**Signature:** `bool TrySelect(object value, out TSlot? slot)`

Looks `value` up in the condition map. Returns `false` and a null slot when the value has no branch.

### NormalizeSelectorValue

**Signature:** `object? NormalizeSelectorValue(object? value)`

Converts `value` onto the current selector type (enum parse with case-insensitive names, or `Convert.ChangeType`). Returns the input unchanged when it cannot be converted. `CurrentValue` normalises its writes the same way, so compare a read-back value with this method before matching it against enum members.

### Install / Uninstall

**Signatures:** `void Install(INodeComponent parent, string memberName)`, `void Uninstall()`

`Install` sets `Parent`, remembers the member name for change notifications, and adds the enumerator to the node helper's `Providers` list when the helper implements `IConditionalSlotProviders`. `Uninstall` removes it, clears the condition map and detaches every slot.

### OnDeserializing / OnDeserialized

**Signatures:** `void OnDeserializing(StreamingContext context)`, `void OnDeserialized(StreamingContext context)`

Serialization hooks, public because a consuming assembly serialises its own closed `SlotEnumerator<TSlot>`. The first clears `Items` and `ConditionMap` before the serializer fills them; the second re-resolves `SelectorType` from `SelectorTypeName`, re-normalises every branch value, re-validates `CurrentValue`, re-seeds the per-type cache and re-attaches the slots to `Parent`.

### GetEnumerator

**Signature:** `IEnumerator<TSlot> GetEnumerator()`

Iterates the slots (not the entries). The non-generic `IEnumerator IEnumerable.GetEnumerator()` is implemented too.

## Explicit interface members

`IConditionalSlotProvider.Slots` returns `Items` as `IReadOnlyList<IConditionalSlot>`; `IConditionalSlotProvider.TrySelect(object, out ISlotComponent?)` forwards to the typed method. These are the erased view used by a caller that does not know `TSlot`.

## Slot registration with the node

When a branch is added and the enumerator has a parent, the slot is registered immediately:

- on a detached node, `parent.StandardCreateSlot(slot)` runs as a plain collection add;
- on an attached node, `parent.CreateSlotCommand.Execute(slot)` submits one undo entry per slot.

The idempotency guard in `StandardCreateSlot` makes a later deferred command dispatch a no-op instead of producing a phantom undo entry.

## Example

```csharp
var node = new NodeDefaultViewModel();
var ports = new SlotEnumerator<SlotDefaultViewModel>();
ports.Install(node, "OutputSlots");

ports.SetSelector(typeof(DayOfWeek));
Console.WriteLine($"{ports.Count} {ports.Items[0].Name} {ports.SelectorType?.Name}");

if (ports.TrySelect(DayOfWeek.Friday, out var friday))
    Console.WriteLine(friday!.State);   // StandBy

ports.CurrentValue = DayOfWeek.Friday;
Console.WriteLine(ports.CurrentValue);  // Friday
```
