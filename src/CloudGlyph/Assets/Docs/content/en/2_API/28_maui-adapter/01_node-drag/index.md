# Node drag

`WorkflowNodeDragBehavior` turns a drag on a node card into `MoveCommand`. On Windows the adapter captures the pointer; on the other platforms the MAUI pan gesture owns the drag once it starts, because native pointer capture may not be available there.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.MAUI`.

## WorkflowNodeDragBehavior

**Signature:** `sealed class WorkflowNodeDragBehavior` (a static attached-property class; no `BindableObject` base)

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Turns a drag on the element into a node move. |
| `CoordinateHostName` | `string?` | `null` | Element whose coordinate space the delta is measured in. |
| `CoordinateHostType` | `Type?` | `null` | Type used to resolve the coordinate host. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, `GetCoordinateHostName` / `SetCoordinateHostName`, `GetCoordinateHostType` / `SetCoordinateHostType`, all taking a `BindableObject`.

```xml
<Grid Grid.Row="0" BackgroundColor="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <Label Text="{Binding Name}" Margin="10,0" VerticalTextAlignment="Center" />
</Grid>
```

**Expected result:** dragging the card moves the bound node; the change is not added to the undo history by default.
