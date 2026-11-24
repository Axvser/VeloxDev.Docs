# Presentation helpers

Namespace: `VeloxDev.WorkflowSystem.AttachedBehaviors`.

These static helpers replace the XAML adapter's element property system with plain data, CSS strings and component-level subscriptions.

## Class: WorkflowCanvasTransformBehavior

`public static class WorkflowCanvasTransformBehavior`

Exposes the content translate as data and as a CSS transform string.

| Signature | Returns | Description |
| --- | --- | --- |
| `GetOffset(ITreeComponent tree)` | `Offset` | `tree.Layout?.ActualOffset`, or a zero offset. |
| `ToCss(Offset offset)` | `string` | `translate({H}px, {V}px)`, always invariant-formatted. |
| `GetTransformStyle(ITreeComponent tree)` | `string` | `ToCss(GetOffset(tree))`. |

The invariant formatting matters: a comma-decimal culture would make the browser drop the whole declaration.

## Class: WorkflowEvents

`public static class WorkflowEvents`

Razor analogue of the XAML attached event sinks. Call the overload from `OnInitialized` / `OnParametersSet` and dispose the subscription when the component is done.

| Signature | Returns | Description |
| --- | --- | --- |
| `Attach(INodeComponent node, INodeEventSink sink)` | `IDisposable?` | Relays node placement and lifetime events; `null` when the helper offers none. |
| `Attach(ISlotComponent slot, ISlotEventSink sink)` | `IDisposable?` | Relays slot channel events. |
| `Attach(ITreeComponent tree, ITreeEventSink sink)` | `IDisposable?` | Relays tree connection events. |

### Example: attach an event sink

```csharp
private IDisposable? _pair;
private INodeEventSink? _sink;

protected override void OnParametersSet()
{
    _pair?.Dispose();
    _pair = Node is { } node && _sink is not null
        ? WorkflowEvents.Attach(node, _sink)
        : null;
}
// Source: source
```

A view reused for another component must dispose the old subscription and re-attach.

## Class: WorkflowGeometryScope

`public static class WorkflowGeometryScope`

Marks a server-side zoom transaction so per-node geometry writers stand down.

| Member | Type | Description |
| --- | --- | --- |
| `IsZooming` | `bool` (get) | True while a zoom transaction is active on the current async flow. |
| `Zoom()` | `IDisposable` | Enters the scope; dispose to leave. |

### Notes

- The depth is held in `AsyncLocal<int>`, so circuits sharing a process cannot observe each other's zoom.
- Entry is counted; nested or re-entrant use is safe.
- During the scope, the single atomic `applyZoomSurface` interop is the only geometry authority.

## Class: WorkflowPresentation

`public static class WorkflowPresentation`

Default Blazor tree palette and input/output slot helpers.

### Properties

| Name | Type | Value |
| --- | --- | --- |
| `MinorGridColor` | `string` | `#2A2D2E` |
| `RulerBackground` | `string` | `#C8252526` converted to CSS |
| `RulerTickColor` | `string` | `#555555` |
| `RulerDividerColor` | `string` | `#3A3D40` |
| `NodeForegroundCss` | `string` | `#DD1E1E1E` converted to CSS |

### Methods

| Signature | Returns | Description |
| --- | --- | --- |
| `ToCss(string value)` | `string` | Converts `#AARRGGBB` to `rgba(...)`; passes `#RRGGBB`, named and `rgb()/rgba()` strings through. |
| `InputSlotsOf(INodeComponent node)` | `IEnumerable<ISlotComponent>` | Pure source slots without a target flag. |
| `OutputSlotsOf(INodeComponent node)` | `IEnumerable<ISlotComponent>` | Slots carrying a target flag. |
| `SlotNamesOf(INodeComponent node)` | `Dictionary<ISlotComponent, string>` | Names from each enumerator's `ConditionalSlot` entry. |

`SlotNamesOf` reads `IConditionalSlotProviders`; it does not reflect over the node's properties by name.

## Class: WorkflowRuntimeIds

`public static class WorkflowRuntimeIds`

Stable process-lifetime ids for workflow components, used by `data-*-id` attributes.

| Signature | Returns | Description |
| --- | --- | --- |
| `Get(object component)` | `string` | Returns the id, assigning a GUID-based one on first use. |
| `TryFind<T>(string? id, out T? value)` | `bool` | Resolves a component back from its id. |
| `Enumerate()` | `IEnumerable<KeyValuePair<object, string>>` | Every registered id, for diagnostics and tests. |

Ids are held in a `ConditionalWeakTable`, so they never keep a component alive.

### Example: stamp a runtime id

```razor
<div data-veloxdev-node-id="@WorkflowRuntimeIds.Get(node)"></div>
```
