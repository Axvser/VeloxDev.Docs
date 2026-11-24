# Conditional slots and providers

An entry pairs a selector value with the slot built for it. A provider supplies the entries when the ports are not enum members, and the node's helper exposes every installed enumerator through one erasure interface.

Namespace: `VeloxDev.WorkflowSystem`, except `SlotSelectorsAttribute` which is in `VeloxDev.AI`.

## IConditionalSlot

**Signature:** `interface IConditionalSlot`

| Member | Type | Description |
| --- | --- | --- |
| `Name` | `string` | Display label for the entry. |
| `Value` | `object?` | Selector value the entry answers to. |
| `Slot` | `ISlotComponent` | The slot built for this entry. |

## ConditionalSlot<T>

**Signature:** `partial class ConditionalSlot<TSlot> : IConditionalSlot where TSlot : ISlotComponent, new()`

| Member | Type | Description |
| --- | --- | --- |
| `Name` | `string` | Label; defaults to empty. |
| `Value` | `object?` | Selector value. |
| `Slot` | `TSlot` | The slot; created by the default constructor of `TSlot`. |
| `IConditionalSlot.Slot` | `ISlotComponent` | Explicit implementation over the typed property. |

## SlotDefinition

**Signature:** `sealed class SlotDefinition(object value, string label = "")`

| Member | Type | Description |
| --- | --- | --- |
| `SlotDefinition(object value, string label = "")` | constructor | Stores the routing key and the label. |
| `Value` | `object` | Routing key used by `TrySelect`. |
| `Label` | `string` | Display name; falls back to `Value` when empty. |

## ISlotProvider

**Signature:** `interface ISlotProvider`

| Member | Type | Description |
| --- | --- | --- |
| `GetSlots()` | `IEnumerable<SlotDefinition>` | Ordered definitions; each becomes one `ConditionalSlot<TSlot>`. |

A provider is a **value**, not a type: passing another instance of the same type to `SetSelector` rebuilds the ports from that instance rather than restoring a snapshot. This is what lets an Agent reshape a node's ports repeatedly. To survive a serialization round trip, annotate the provider with `[Archivable]` and make its model serializable.

## IConditionalSlotProvider<T>

**Signature:** `interface IConditionalSlotProvider<TSlot> : IEnumerable<TSlot> where TSlot : ISlotComponent, new()`

| Member | Type | Description |
| --- | --- | --- |
| `Parent` | `INodeComponent?` | Installed node, or null. |
| `SelectorTypeName` | `string` | Stored selector type name. |
| `Items` | `ObservableCollection<ConditionalSlot<TSlot>>` | The branches. |
| `CurrentValue` | `object?` | Selected value. |
| `TrySelect(object value, out TSlot? slot)` | `bool` | Routing lookup. |
| `SetSelector(object? selector)` | `void` | Switches the selector. |
| `Install(INodeComponent parent, string memberName)` | `void` | Binds to a node. |
| `Uninstall()` | `void` | Detaches. |

## IConditionalSlotProvider

**Signature:** `interface IConditionalSlotProvider` — the type-erased view.

| Member | Type | Description |
| --- | --- | --- |
| `Parent` | `INodeComponent?` | Installed node. |
| `SelectorTypeName` | `string` | Stored type name. |
| `SelectorType` | `Type?` | Resolved selector type. |
| `CurrentValue` | `object?` | Selected value. |
| `Slots` | `IReadOnlyList<IConditionalSlot>` | Current branches. |
| `TrySelect(object value, out ISlotComponent? slot)` | `bool` | Routing lookup. |
| `SetSelector(object? selector)` | `void` | Switches the selector. |

## IConditionalSlotProviders

**Signature:** `interface IConditionalSlotProviders`

| Member | Type | Description |
| --- | --- | --- |
| `Providers` | `IList<IConditionalSlotProvider>` | The node's enumerators, in installation order. |

`NodeHelper<T>` implements this interface. `SlotEnumerator<TSlot>.Install` adds to `Providers` and `Uninstall` removes, so readers should treat the list as read-only.

## SlotSelectorsAttribute

**Signature:** `sealed class SlotSelectorsAttribute : Attribute`, `AttributeTargets.Property | AttributeTargets.Field`.

| Member | Type | Description |
| --- | --- | --- |
| `SlotSelectorsAttribute(params Type[] allowedEnumTypes)` | constructor | Compile-time-safe list; also derives `AllowedEnumTypeNames`. |
| `SlotSelectorsAttribute(params string[] allowedEnumTypeNames)` | constructor | Serialization-friendly names; `AllowedEnumTypes` stays empty. |
| `AllowedEnumTypes` | `Type[]` | Permitted selector types. |
| `AllowedEnumTypeNames` | `string[]` | Fully-qualified names, suitable for serialization. |

The attribute declares which selector types the **Agent tools** (`ListSlotProperties`, `SetEnumSlotCollection`) may use for that member. It does not drive the enumerator: direct code calls `SetSelector` with any enum, `bool` or provider. The annotated property is rejected by `PatchNodeProperties`; the enum-slot tool is the sanctioned mutation path.

An empty list on both members means any type is accepted.

## Example

```csharp
public sealed class PortProvider(params string[] names) : ISlotProvider
{
    public IEnumerable<SlotDefinition> GetSlots()
        => names.Select(name => new SlotDefinition(name, name));
}

var node = new NodeDefaultViewModel();
var ports = new SlotEnumerator<SlotDefaultViewModel>();
ports.Install(node, "OutputSlots");
ports.SetSelector(new PortProvider("stats", "dist", "anomalies"));

Console.WriteLine(string.Join(",", ports.Items.Select(i => i.Name))); // stats,dist,anomalies
Console.WriteLine(ports.TrySelect("dist", out var dist));            // True

// Rebuild from another instance of the same provider type: branches pair by name.
ports.SetSelector(new PortProvider("stats", "trend"));
Console.WriteLine(ports.Count);                                      // 2
```
