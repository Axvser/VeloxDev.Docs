# Spatial virtualization

Virtualization is a property of the tree helper. A helper built with a cell size installs a spatial map and maintains `VisibleItems`; a helper built with the parameterless constructor keeps the set empty and renders everything through direct bindings.

## TreeHelper

```csharp
public class TreeHelper : TreeHelper<ITreeComponent>
```

| Constructor | Behaviour |
|---|---|
| `TreeHelper()` | Virtualization off; `VisibleItems` stays empty. |
| `TreeHelper(double cellSize)` | Virtualization on; the cell size is the spatial grid's cell in canvas units. Starts the shared `TreeHelper` tick channel at 10 fps when it is not running. |

`TreeHelper<T>` has the same two constructors and is declared `partial` so the generators add tick and property plumbing.

### Virtualization members

| Member | Type | Description |
|---|---|---|
| `VisibleItems` | `ObservableCollection<IWorkflowComponent>` | The visible set: the virtual link, nodes near the viewport, and links whose endpoints are in the query. Generated property with change tracking. |
| `Viewport` | `Viewport` | Current viewport. Assigning it calls `Component?.Virtualize(value)`. |
| `Component` | `T?` | Installed tree, when it matches `T`. |
| `Input` | `InputRelay` | Routed input for the tree. |
| `NodeAdded` / `NodeRemoved` | `EventHandler<INodeComponent>` | Raised when a node enters or leaves the tree. |
| `LinkAdded` / `LinkRemoved` | `EventHandler<ILinkComponent>` | Raised when a link enters or leaves the tree. |
| `VisibleItemAdded` / `VisibleItemRemoved` | `EventHandler<IWorkflowComponent>` | Raised as the visible set changes. |

| Method | Description |
|---|---|
| `Install(ITreeComponent tree)` | Resets the visible set, subscribes to node/link collections, captures `SynchronizationContext.Current` unless set explicitly, and enables the spatial map through `EnableMap(CellSize, VisibleItems)`. |
| `Uninstall(ITreeComponent tree)` | Unsubscribes, clears the map (`ClearMap`), clears the visible set, and drops an auto-captured context. |
| `Virtualize(Viewport viewport)` | Forwards to `Component?.Virtualize(viewport)`. |
| `WithSynchronizationContext(SynchronizationContext? context)` | Binds virtualization passes to a UI context. `null` means run inline on the tick thread. An explicit value survives later installations. Returns the helper. |
| `MarkDirty()` | Requests one merged virtualization pass on the next tick. |

Node geometry changes do not mark the visible set dirty; a drag repaints the card and the visible set waits for the next scroll, zoom, or `MarkDirty()`.

## Viewport

```csharp
public readonly struct Viewport : IEquatable<Viewport>, ISampleable
```

| Member | Type | Description |
|---|---|---|
| `Viewport(double left, double top, double width, double height)` | constructor | Creates a viewport. |
| `Empty` | `static Viewport` | The default value. |
| `Horizontal` / `Vertical` | `double` | Left and top edges. |
| `Width` / `Height` | `double` | Size. |
| `Right` / `Bottom` | `double` | `Horizontal + Width` and `Vertical + Height`. |
| `IsEmpty` | `bool` | Width or height is at most zero. |

| Method | Description |
|---|---|
| `IntersectsWith(double left, double top, double width, double height)` | Rectangle intersection test. |
| `IntersectsWith(Viewport other)` | Viewport intersection test. |
| `Contains(double x, double y)` | Point test. |
| `Contains(Viewport other)` | Containment test. |
| `Union(Viewport a, Viewport b)` | Union of two viewports. |
| `GetAnimatableMembers()` / `CreateFrameValue(...)` | Sampling support inherited from `ISampleable`. |

Value equality, `==`, `!=`, `GetHashCode`, and `ToString` are implemented.

## ISpatialMap and ISpatialBoundsProvider

```csharp
public interface ISpatialMap<T> where T : class, ISpatialBoundsProvider
{
    Viewport Bounds { get; }
    void Insert(T item);
    void Remove(T item);
    IEnumerable<T> Query(Viewport viewport);
    void Clear();
}

public interface ISpatialBoundsProvider : INotifyPropertyChanged
{
    Viewport Bounds { get; }
}
```

A bounds provider must raise `PropertyChanged` with the name `"Bounds"` when its geometry changes.

## SpatialGridHashMap

```csharp
public class SpatialGridHashMap<T>(double cellSize) : ISpatialMap<T>
    where T : class, ISpatialBoundsProvider
```

The cell size clamps to at least 1.

| Member | Description |
|---|---|
| `Bounds` | Minimal viewport covering every registered item; `Viewport.Empty` when none. |
| `Insert(T item)` | Registers the item and subscribes to its `PropertyChanged`. Empty or NaN bounds are tracked but indexed later. |
| `Remove(T item)` | Unregisters and unsubscribes. |
| `Query(Viewport viewport)` | Lazily yields intersecting items. Zero-size items are tested as points. Flushes deferred and late-measured entries before answering. |
| `Clear()` | Unsubscribes and clears items, cells, and bounds. |

## CellKey

```csharp
public readonly struct CellKey(int x, int y) : IEquatable<CellKey>
```

| Member | Description |
|---|---|
| `X` / `Y` | Column and row indices. |
| `Equals(CellKey)` / `Equals(object?)` / `GetHashCode()` | Value equality. |
| `ToString()` | `CellKey(X, Y)`. |
| `==` / `!=` | Operators. |

## WorkflowSpatialManager

```csharp
public sealed class WorkflowSpatialManager : IDisposable
```

| Member | Description |
|---|---|
| `WorkflowSpatialManager(ITreeComponent tree, double cellSize)` | Indexes existing nodes and links and subscribes to helper node/link events. Throws `ArgumentNullException` for a null tree. |
| `GlobalBounds` | Union of the node map and the node-pair map. |
| `QueryNodes(Viewport viewport)` | Lazily yields individually visible nodes intersecting the viewport. |
| `Dispose()` | Idempotent; unsubscribes, disposes providers, and clears the maps. |

The manager lives inside the tree helper; hosts normally reach virtualization through `TreeHelper` and never construct it.

## WorkflowSpatialEx

```csharp
namespace VeloxDev.WorkflowSystem.StandardEx;

public static class WorkflowSpatialEx
```

| Signature | Returns | Description |
|---|---|---|
| `EnableMap<T>(this ITreeComponent tree, double cellSize, T observable)` | `int` | Enables virtualization and binds the visible collection. `-1` for a non-positive cell size, `0` when already enabled, `1` on success. |
| `Virtualize(this ITreeComponent tree, Viewport viewport)` | `void` | Rebuilds the visible collection: virtual link plus visible nodes and links. No-op for an empty viewport; throws `ArgumentNullException` when the map was not enabled. |
| `ClearMap(this ITreeComponent tree)` | `int` | Removes the tree from its maps and observables. Bitmask: 1 manager removed, 2 manager not removed, 4 observable removed, 8 observable not removed. |
| `SetVirtualizeInset(this ITreeComponent tree, double left = 0, double top = 0, double right = 0, double bottom = 0)` | `void` | Inflates the query on each edge without moving the authoritative viewport. Negative values clamp to zero. Used for the ruler band. |
| `QueryNodes(this ITreeComponent tree, Viewport viewport)` | `IEnumerable<INodeComponent>` | Lazily returns intersecting nodes; throws when the map was not enabled. |
| `QueryNodes(this ITreeComponent tree, Anchor from, Anchor to)` | `IReadOnlyList<INodeComponent>` | Materialised marquee selection between two corners; either order works. |

## WorkflowNodeScaleTracker

```csharp
public sealed class WorkflowNodeScaleTracker
```

Watches the parent tree's `CanvasLayout.Scale`. When the scale changes it invokes a callback and calls `MarkDirty()`, so a node can re-raise `Anchor` and `Size` for re-virtualization.

| Member | Description |
|---|---|
| `Attach(ITreeComponent? tree, Action onScaleDirty)` | Attaches to the tree. `null` detaches. Passing the same tree again only replaces the callback. |
| `Detach()` | Unsubscribes from the tree and layout and clears the callback. |

The tracker follows a replaced `Layout` as well as a replaced tree. A node view uses it when zoom changes its effective size but no node property was assigned.

## Notes

- `VisibleItems` is bound to UI, so the tick thread must not touch it. The helper posts the pass back to the captured context.
- A helper installed off the UI thread must be given the context explicitly; passing `null` is the correct choice for a service or a headless test.
- `SpatialGridHashMap.Query` calls `EnsureIndexed` first, so an item measured after registration is found by the next query.
