# Dynamic slot enumeration

A `SlotEnumerator<TSlot>` maps one selector value to one slot. The selector can be an enum, `bool`, or an `ISlotProvider` instance; switching it re-materialises the whole port set as one undoable step.

- [Slot enumerator](00_slot-enumerator/index.md) — `SlotEnumerator<TSlot>`, its selection state and re-materialisation rules.
- [Conditional slots and providers](01_conditional-slots/index.md) — `ConditionalSlot<TSlot>`, `SlotDefinition`, `ISlotProvider`, the provider interfaces and `[SlotSelectors]`.

```csharp
var node = new NodeDefaultViewModel();
var ports = new SlotEnumerator<SlotDefaultViewModel>();
ports.Install(node, nameof(ports));
ports.SetSelector(typeof(DayOfWeek));

Console.WriteLine(ports.Count);      // 7
Console.WriteLine(ports.TrySelect(DayOfWeek.Monday, out var slot));
```

For a task-oriented walkthrough, see [Dynamic slot enumeration](../../1_QuickStart/03_dynamic-slot-enumeration/index.md).
