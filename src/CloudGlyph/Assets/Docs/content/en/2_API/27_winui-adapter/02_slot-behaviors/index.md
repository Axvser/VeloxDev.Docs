# Slot behaviors

The connection behavior uses a pointer-capture release to emulate the missing tunnel phase; the slot-layout behavior measures ports **canvas-local** and writes their anchors through `SlotAnchorFromCanvasLocal`.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WinUI`.

## WorkflowSlotConnectionBehavior

**Signature:** `sealed class WorkflowSlotConnectionBehavior : DependencyObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Enables press-to-send / release-to-receive. |

Accessors: `GetIsEnabled` / `SetIsEnabled`.

The two standard commands are unchanged. The behavior decides nothing about legality; that is `ITreeHelper.ValidateConnection` and the `ITreeEvents.Connecting` veto.

```xml
<Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
```

**Expected result:** press one port and release on another to create a link; release on empty canvas cancels.

## WorkflowSlotLayoutBehavior

**Signature:** `sealed class WorkflowSlotLayoutBehavior : DependencyObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Measures named ports and writes anchors. |
| `SlotNames` | `string?` | `null` | Named single ports. |
| `SlotEnumeratorNames` | `string?` | `null` | Named enumerators whose items expose ports. |
| `CoordinateHostName` | `string?` | `null` | Element whose coordinate space the anchors use. |
| `CoordinateHostType` | `Type?` | `null` | Type used to resolve the coordinate host. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, `GetSlotNames` / `SetSlotNames`, `GetSlotEnumeratorNames` / `SetSlotEnumeratorNames`, `GetCoordinateHostName` / `SetCoordinateHostName`, `GetCoordinateHostType` / `SetCoordinateHostType`. WinUI has no public `Refresh` on this behavior; the surface refreshes it on its own layout pass.

Anchors on this adapter are measured **canvas-local** and written through `SlotAnchorFromCanvasLocal`. Using the visual-centre form subtracts `ActualOffset` a second time and shifts every link by a constant.

```xml
<Grid behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
      behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
      behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
      behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
```

**Expected result:** a link meets its ports at 100% and at 40%, and does not shift when the canvas is panned.
