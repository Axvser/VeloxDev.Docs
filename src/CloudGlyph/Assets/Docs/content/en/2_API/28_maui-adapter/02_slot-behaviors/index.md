# Slot behaviors

The connection behavior starts and completes a connection drag, and on MAUI also reports the candidate receiver because the shared link overlay cannot hit-test a slot. The layout behavior measures ports and writes their anchors.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.MAUI`.

## WorkflowSlotConnectionBehavior

**Signature:** `sealed class WorkflowSlotConnectionBehavior` (a static attached-property class)

| Member | Signature | Description |
| --- | --- | --- |
| `IsEnabledProperty` | `BindableProperty` | Attached switch, default `false`. |
| `GetIsEnabled(BindableObject)` / `SetIsEnabled(BindableObject, bool)` | accessors | Reads or writes the switch. |
| `SetIsDraggingConnection(bool isDraggingConnection)` | `static void` | Tells the behavior whether a connection drag is in progress, so it can report the candidate receiver. |

On Windows the adapter captures the pointer; on the other platforms it lets the MAUI pan gesture own the drag once it starts. The two standard commands are unchanged, and the behavior decides nothing about legality.

```xml
<Ellipse x:Name="PART_InputSlot" Grid.Row="1" BindingContext="{Binding InputSlot}"
         WidthRequest="14" HeightRequest="14" Fill="#FF1E1E1E" Stroke="White"
         HorizontalOptions="Start" VerticalOptions="Center"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

**Expected result:** press a port and release on another to connect; release on empty canvas to cancel.

## WorkflowSlotLayoutBehavior

**Signature:** `sealed class WorkflowSlotLayoutBehavior` (a static attached-property class)

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Measures named ports and writes anchors. |
| `SlotNames` | `string?` | `null` | Named single ports. |
| `SlotEnumeratorNames` | `string?` | `null` | Named enumerators whose items expose ports. |
| `CoordinateHostName` | `string?` | `null` | Element whose coordinate space the anchors use. |
| `CoordinateHostType` | `Type?` | `null` | Type used to resolve the coordinate host. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, `GetSlotNames` / `SetSlotNames`, `GetSlotEnumeratorNames` / `SetSlotEnumeratorNames`, `GetCoordinateHostName` / `SetCoordinateHostName`, `GetCoordinateHostType` / `SetCoordinateHostType`.

| Method | Signature | Description |
| --- | --- | --- |
| `Refresh` | `static void Refresh(ContentView control)` | Re-measures every named port against the current viewport. |

```xml
<Border behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
        behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
        behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
        behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
```

**Expected result:** after layout, each port's `ISlotComponent.Anchor` matches its visual centre; a link drawn from those anchors meets the ports.
