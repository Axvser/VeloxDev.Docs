# Pipeline

`MinimapPipelineCore` subscribes to tree changes, debounces them into one pass, maps node and viewport rectangles into the minimap, and turns a press or drag into scroll offsets. `MinimapHostCore` holds its three platform layers.

## MinimapHostCore

```csharp
public abstract class MinimapHostCore<TSurface, TRenderer, TViewport, TInput>
    where TRenderer : class, IMinimapRenderer<TSurface>
    where TViewport : class, IMinimapViewportHost
    where TInput : class, IMinimapInputHost
```

| Member | Type | Description |
|---|---|---|
| `protected MinimapHostCore(TRenderer renderer, TViewport viewport, TInput input)` | constructor | Groups the three layers. Throws `ArgumentNullException` for any null layer. |
| `Renderer` | `TRenderer` | Draws a pass. |
| `Viewport` | `TViewport` | Reads and writes scroll state. |
| `Input` | `TInput` | Pointer state and capture. |

## MinimapPipelineCore

```csharp
public class MinimapPipelineCore<TSurface, TRenderer, TViewport, TInput>
    : MinimapHostCore<TSurface, TRenderer, TViewport, TInput>, IDisposable
    where TRenderer : class, IMinimapRenderer<TSurface>
    where TViewport : class, IMinimapViewportHost
    where TInput : class, IMinimapInputHost
```

### Constructor

| Signature | Description |
|---|---|
| `MinimapPipelineCore(TRenderer renderer, TViewport viewport, TInput input, MinimapMetrics? metrics = null)` | `null` metrics means `MinimapMetrics.Default`. The pipeline starts visible and dirty. |

### Properties

| Member | Type | Description |
|---|---|---|
| `Metrics` | `MinimapMetrics` | Placement and style inputs. The setter ignores an equal value; a change marks the pipeline dirty. |
| `IsVisible` | `bool` | Whether a pass draws; default `true`. |
| `Tree` | `ITreeComponent?` | Rendered tree. The setter unsubscribes the old tree, subscribes the new one, and invalidates. |
| `IsDirty` | `bool` | Whether the mapping must be rebuilt. |
| `IsDragging` | `bool` | Whether a drag is in progress. |
| `ContentBounds` | `WorkflowBounds` | Bounds of all node rectangles, canvas-local. |
| `ViewportBounds` | `WorkflowBounds` | Current viewport, canvas-local. |
| `DrawContext` | `MinimapDrawContext?` | The last built pass; `null` before the first pass or for an empty tree. |
| `SubscribedNodeCount` | `int` | Nodes currently tracked. |
| `SubscribedLinkCount` | `int` | Links currently tracked. |
| `MinimapRect` | `WorkflowBounds` | Placed rectangle, computed from `Metrics` in the top-right corner. |

### Event

| Event | Description |
|---|---|
| `RenderRequested` | `EventHandler` raised by `Invalidate`, once per call. |

### Methods

| Signature | Description |
|---|---|
| `Invalidate()` | Marks dirty and raises `RenderRequested`. Disposed-safe. |
| `Refresh()` | Returns early when disposed or clean; otherwise clears the flag and rebuilds `DrawContext`. |
| `Render(TSurface surface)` | Returns when disposed or hidden; refreshes, then calls `Renderer.Render(surface, DrawContext)`. The renderer runs on every visible pass, not only dirty ones. |
| `HitTest(double x, double y)` | Whether the point is inside `Input.ClampRect` when non-empty, otherwise inside `MinimapRect`. |
| `PointerPressed()` | Requires a press inside the map; refreshes, centres the viewport on the point, starts a drag, and captures. Returns whether a drag started. |
| `PointerMoved()` | While dragging, centres the viewport on the current pointer position. |
| `PointerReleased()` | Ends a drag and releases capture. No-op when not dragging. |
| `PointerCaptureLost()` | Ends a drag and releases capture. No-op when not dragging. |
| `Dispose()` | Unsubscribes the tree and drops the draw context. |

### Subscription rules

The pipeline listens to `INotifyCollectionChanged` on the tree's nodes and links. On a node it listens for `Anchor` and `Size`; on a link it listens to the sender and receiver slots' `Anchor`. Other property names do not invalidate the map, so moving an unrelated property costs nothing.

## MinimapDrawContext

```csharp
public sealed class MinimapDrawContext
```

One immutable-by-convention pass. Create it with an object initialiser; the pipeline builds it for you.

| Property | Type | Description |
|---|---|---|
| `Tree` | `ITreeComponent?` | Rendered tree. |
| `ContentBounds` | `WorkflowBounds` | Canvas-local bounds of all nodes. |
| `ViewportBounds` | `WorkflowBounds` | Canvas-local viewport. |
| `Nodes` | `IReadOnlyList<WorkflowBounds>` | Canvas-local node rectangles; defaults to an empty array. |
| `MappedNodes` | `IReadOnlyList<WorkflowBounds>` | Minimap-local thumbnails, already padded and minimum-sized; defaults to an empty array. |
| `MappedViewport` | `WorkflowBounds` | Minimap-local viewport indicator. |
| `MinimapWidth` / `MinimapHeight` | `double` | Placed size. |
| `Padding` | `double` | Inner padding. |
| `OriginX` / `OriginY` | `double` | Content origin inside the minimap. |
| `Scale` | `double` | Content-to-minimap scale. |
| `NodeCornerRadius` / `MinimapCornerRadius` | `double` | Corner radii. |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | Corner edges. |
| `MinimapMargin` | `double` | Corner gap. |

| Member | Type | Description |
|---|---|---|
| `GetMinimapRect(double minimumSize)` | `WorkflowBounds` | Places the requested size in the available corner. |
| `HasContent` | `bool` | `!ContentBounds.IsEmpty`. |
| `HasViewport` | `bool` | `!ViewportBounds.IsEmpty`. |

## Notes

- A burst of property changes costs one rebuild because `Invalidate` only sets a flag and raises a request.
- `Render` calls the renderer even when the mapping is clean; a platform may need to repaint after a resize.
- The pipeline's mapping reads node `Anchor` and `Size` only; it never needs a view to exist.
