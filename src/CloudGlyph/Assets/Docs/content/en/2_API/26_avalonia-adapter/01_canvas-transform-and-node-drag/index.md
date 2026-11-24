# Canvas transform and node drag

The Avalonia counterparts of the WPF pair. The transform behavior carries an `ITransform?` attached value that node and link templates bind their `RenderTransform` to; the drag behavior executes `MoveCommand` with the pointer delta.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.Avalonia`.

## WorkflowCanvasTransformBehavior

**Signature:** `sealed class WorkflowCanvasTransformBehavior : AvaloniaObject`

| Member | Signature | Description |
| --- | --- | --- |
| `TransformProperty` | `AttachedProperty<ITransform?>` | The attached transform. |
| `GetTransform(AvaloniaObject element)` | `static ITransform?` | Reads the transform. |
| `SetTransform(AvaloniaObject element, ITransform? value)` | `static void` | Writes the transform. |

The property is a notification carrier only: the host control deliberately receives no render transform; node and link views bind their own. With compiled bindings the binding is written as:

```xml
RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
```

## WorkflowNodeDragBehavior

**Signature:** `sealed class WorkflowNodeDragBehavior : AvaloniaObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Turns a drag on the element into a node move. |
| `CoordinateHostName` | `string?` | `null` | Element whose coordinate space the delta is measured in. |
| `CoordinateHostType` | `Type?` | `null` | Type used to resolve the coordinate host. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, `GetCoordinateHostName` / `SetCoordinateHostName`, `GetCoordinateHostType` / `SetCoordinateHostType`, all taking `AvaloniaObject`.

```xml
<Grid Height="32" VerticalAlignment="Top" Background="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <TextBlock Text="{Binding Name}" Margin="10,8" />
</Grid>
```

**Expected result:** dragging the element moves the bound node; the node's `MoveCommand` is executed, and the change is not pushed to the undo history by default.
