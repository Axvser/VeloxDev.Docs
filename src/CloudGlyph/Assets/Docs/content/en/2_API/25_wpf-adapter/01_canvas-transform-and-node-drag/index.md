# Canvas transform and node drag

Two small attached behaviors. The transform behavior is a value carrier that node and link templates bind their `RenderTransform` to; the drag behavior turns a drag on a node into `MoveCommand`.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WPF`.

## WorkflowCanvasTransformBehavior

**Signature:** `static class WorkflowCanvasTransformBehavior`

| Member | Signature | Description |
| --- | --- | --- |
| `TransformProperty` | `DependencyProperty` | The attached property carrying the canvas transform. |
| `GetTransform(UIElement element)` | `static Transform?` | Reads the transform. |
| `SetTransform(UIElement element, Transform? value)` | `static void` | Writes the transform. |

The surface writes the current transform; templates bind to it. The binding must sit on the `DataTemplate` root, because an ancestor lookup made from inside a nested view resolves against the item's own tree:

```xml
RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                          Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
```

## WorkflowNodeDragBehavior

**Signature:** `sealed class WorkflowNodeDragBehavior : DependencyObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Turns a drag on the element into a node move. |
| `CoordinateHostName` | `string?` | `null` | The element whose coordinate space the drag delta is measured in. |
| `CoordinateHostType` | `Type?` | `null` | A type used to resolve the coordinate host when a name is not supplied. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, `GetCoordinateHostName` / `SetCoordinateHostName`, `GetCoordinateHostType` / `SetCoordinateHostType`.

The behavior executes the node's `MoveCommand` with the drag delta. `Move` / `SetAnchor` / `SetSize` are not pushed through the undo history by default, so a plain drag is not undoable unless the host submits the change.

```xml
<Grid Grid.Row="0" Background="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <TextBlock Text="{Binding Name}" VerticalAlignment="Center" Margin="10,0" />
</Grid>
```

**Expected result:** dragging the element moves the bound node by the pointer delta measured in the `PART_Canvas` space.
