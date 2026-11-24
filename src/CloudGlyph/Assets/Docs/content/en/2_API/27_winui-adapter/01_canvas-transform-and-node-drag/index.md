# Canvas transform and node drag

The transform behavior carries a `Transform?` attached value for views that bind their `RenderTransform`; the surface itself does not use it for panning on WinUI. The drag behavior turns a drag into `MoveCommand`.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors`, assembly `VeloxDev.WinUI`.

## WorkflowCanvasTransformBehavior

**Signature:** `static class WorkflowCanvasTransformBehavior`

| Member | Signature | Description |
| --- | --- | --- |
| `TransformProperty` | `DependencyProperty` | The attached transform. |
| `GetTransform(UIElement element)` | `static Transform?` | Reads the transform. |
| `SetTransform(UIElement element, Transform? value)` | `static void` | Writes the transform. |

The surface moves the canvas by composition translation; this property exists for a view that prefers a render transform.

## WorkflowNodeDragBehavior

**Signature:** `sealed class WorkflowNodeDragBehavior : DependencyObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | Turns a drag on the element into a node move. |
| `CoordinateHostName` | `string?` | `null` | Element whose coordinate space the delta is measured in. |
| `CoordinateHostType` | `Type?` | `null` | Type used to resolve the coordinate host. |

Accessors: `GetIsEnabled` / `SetIsEnabled`, `GetCoordinateHostName` / `SetCoordinateHostName`, `GetCoordinateHostType` / `SetCoordinateHostType`.

The behavior routes the press before starting the gesture, because WinUI has no tunnel/preview pointer phase. A subscriber that sets `PreventDefault` on the press keeps the drag from starting.

```xml
<Grid Height="32" VerticalAlignment="Top" Background="Transparent"
      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
    <TextBlock Text="{Binding Name}" Margin="10,8" />
</Grid>
```

**Expected result:** dragging the element moves the bound node; the press is routed through `WorkflowInput` first, so a host can refuse the gesture.
