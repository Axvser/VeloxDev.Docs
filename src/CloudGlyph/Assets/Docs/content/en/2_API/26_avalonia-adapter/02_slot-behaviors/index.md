# Slot behaviors

The connection behavior starts and completes a connection drag; the slot-layout behavior measures ports and writes their `Anchor`. Avalonia's adapter releases pointer capture on press so the release can reach the receiving port.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.Avalonia`.

## WorkflowSlotConnectionBehavior

**Signature:** `sealed class WorkflowSlotConnectionBehavior : AvaloniaObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Enables press-to-send / release-to-receive. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, taking `AvaloniaObject`.

The behavior executes the two standard commands and decides nothing about legitimacy; that is `ITreeHelper.ValidateConnection` and the `ITreeEvents.Connecting` veto.

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

**Expected result:** press one port and release on another to create a link; release on empty canvas clears the preview.

## WorkflowSlotLayoutBehavior

**Signature:** `sealed class WorkflowSlotLayoutBehavior : AvaloniaObject`

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
| `Refresh` | `static void Refresh(UserControl control)` | Re-measures every named port. |

The behavior measures each port in the scroll space through `SlotLayoutPipelineCore`, skipping ports whose `Bounds` are not yet measured.

```xml
<Grid behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
      behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
      behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
      behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
```

**Expected result:** after layout, each port's `ISlotComponent.Anchor` matches its visual centre in the canvas space, so a link drawn from those anchors meets the ports.
