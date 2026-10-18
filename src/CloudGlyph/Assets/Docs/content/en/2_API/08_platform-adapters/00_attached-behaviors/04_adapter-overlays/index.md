# API — Attached Behaviors · Adapter-Specific Overlays & Hosts

Beyond the shared behavior set, some adapters ship additional workflow view types that replace or extend a piece of the common surface.

## Class: `WorkflowLinkOverlay` (MAUI)

MAUI draws, in one viewport-sized `GraphicsView`, the links that have **no view of their own** — the immediate-mode hosts and the frames before a pooled link view has materialized. A link that published its curve together with the control that drew it is painted by that control and skipped here. `Src/Adapters/VeloxDev.MAUI/Attached/Workflow/WorkflowLinkOverlay.cs`.

```csharp
public sealed class WorkflowLinkOverlay : GraphicsView
```

Bindable properties / CLR properties:

| Property | Type | Description |
|---|---|---|
| `WorkflowTree` | `IWorkflowTreeViewModel?` | Tree whose links are drawn. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Scroll offsets (fed by the surface). |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Canvas content offset. |
| `RulerThickness` | `double` | Ruler band inset to skip when drawing. |
| `LinkLineColor` | `Color?` | Solid link stroke. |
| `VirtualLineColor` | `Color?` | Stroke used for virtual/out-of-reach link segments. |
| `StrokeWidth` | `double` | Link stroke width. |
| `VirtualValidTargetColor` / `VirtualInvalidTargetColor` | `Color?` | Rubber-band colors while the preview candidate is valid / invalid (`ConnectionPreviewState`). |
| `LinkFlowEnabled` | `bool` | Toggles the travelling-light animation along each curve. |
| `InteractionSource` | `View?` | The view already on the surface's input path that forwards hover/press to the hit test (the overlay itself stays `InputTransparent`). |

The overlay draws each link as one cubic Bézier with the MAUI graphics `IDrawable` model (`Draw(ICanvas canvas, RectF dirtyRect)`); the travelling light is cut out of that curve by arc length rather than mapped along a polyline. It is paint-only (`VisualElement.InputTransparent` stays `true`, so a viewport-sized view cannot swallow the canvas gestures); interaction is driven through `InteractionSource` — the hit test tracks which link the pointer is on, `Delete` removes it, and a right press (or, off Windows, a long press) is routed through `WorkflowInput.For(tree).Route(...)` as a `PointerPressedEventArgs`, so the host surface can open its own menu.

**Hover feedback is the host's**, and this layer paints resting links only. A host that wants a hovered link to look different subscribes the tree's `IInputEvents` and draws its own layer above this one, from the curve the link published (`ILinkHitTestable.Curve`) — so the two can never disagree about where the line is. *Exact drag/reroute semantics `*inferred*` — not exercised by an automated demo.*

## Class: `WorkflowLinkBounds` (Jalium)

Jalium's link views are positioned from their curve points rather than measured from a visual. `Src/Adapters/VeloxDev.Jalium/Attached/Workflow/WorkflowLinkBounds.cs` is the static helper that does it:

```csharp
public static class WorkflowLinkBounds
{
    public static bool Apply(
        FrameworkElement view,
        IReadOnlyList<Point> canvasLocalPoints,
        out double originX,
        out double originY);
}
```

It returns `false` for an empty point list; otherwise it computes the point bounds, sets the view's size and position (`Canvas.Left` / `Canvas.Top`), reports the origin, and returns `true`.

## Jalium template-supplied pieces

Jalium does **not** ship a composite `WorkflowTreeView`, per-role attachments, or a grid-decorator class in the adapter. Its surface is the shared static `WorkflowSurfaceBehavior` (documented on the [surface](../00_surface/index.md) page), and the `dotnet new` templates supply the rest:

- `jalium-v-decorator` generates a `Grid` subclass implementing `IWorkflowGridDecorator`, with `RulerThickness` (36), `GridStep` (40), `MajorLineEvery` (5), the grid/ruler palette, and the five interface offset members.
- `jalium-v-selector` generates a `DataTemplateSelector` with `NodeTemplate` / `SlotTemplate` / `LinkTemplate` / `TreeTemplate`, assigned to `ViewPool.TemplateSelector`.
- `jalium-v-tree` generates a `UserControl` that names `PART_ScrollViewer` / `PART_Canvas` / `PART_GridDecorator` / `PART_SurfaceBorder` / `PART_MinimapOverlay` and re-exposes the surface's `CanvasTransform` as a CLR property, because Jalium bindings cannot address attached properties.

## Class: `WorkflowEvents` (WPF / WinUI / Avalonia / MAUI / Jalium)

Binds a component's model events to a host object without one attached property per event. Source: `Src/Adapters/<Adapter>/Attached/Workflow/WorkflowEvents.cs`.

| Attached property | Type | Forwarded by |
|---|---|---|
| `Node` | `IWorkflowNodeEventSink?` | `WorkflowEventRelay` |
| `Slot` | `IWorkflowSlotEventSink?` | `WorkflowEventRelay` |
| `Tree` | `IWorkflowTreeEventSink?` | `WorkflowEventRelay` |

Each has the usual `Get*` / `Set*` accessors. Attach it to the view whose `DataContext` is the component: the subscription follows the data context, so a pooled view handed to another node drops the old subscription and makes a new one.

## Class: `WorkflowBindingExtensions` (WinForms)

Static subscription helpers for WinForms views (`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowBindingExtensions.cs`). Each returns an `IDisposable` that also ends when the control is disposed.

| Method | Signature |
|---|---|
| `Bind` | `static IDisposable Bind<TModel>(this Control control, TModel? model, Action<Control, TModel> apply)` |
| `Bind` (projected) | `static IDisposable Bind<TModel, TValue>(this Control control, TModel? model, Func<TModel, TValue> selector, Action<Control, TValue> apply)` |
| `BindCollection` | `static IDisposable BindCollection(this Control control, INotifyCollectionChanged? source, Action<Control, NotifyCollectionChangedEventArgs> onChange)` |

The returned subscription marshals to the control's thread and detaches on `Control.Disposed`.

## WinForms per-role attachments

WinForms has no base class for the three view roles; each generated view calls `Attach(Control)` on itself and keeps drawing the control. All three live in `VeloxDev.WorkflowSystem.AttachedBehaviors`, are sealed, and keep **one instance per control** in a `ConditionalWeakTable` — `Attach` is idempotent and `For` returns the existing instance.

### Class: `WorkflowNodeAttachment`

`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowNodeAttachment.cs`; implements `IWorkflowSurfaceNodeView`.

**Static methods**

| Method | Signature |
|---|---|
| `Attach` | `static WorkflowNodeAttachment Attach(Control target)` — throws `ArgumentNullException` for `null` |
| `For` | `static WorkflowNodeAttachment? For(Control target)` |
| `DisposeChildren` | `static void DisposeChildren(Control parent)` |
| `ParseColor` | `static Color ParseColor(string hex)` |

**Properties**

| Property | Type | Access | Description |
|---|---|---|---|
| `Node` | `IWorkflowNodeViewModel?` | get/set | Bound node; setting it rebinds events and places the card. |
| `Title` | `string` | get | Title read through `NodeTitle`. |
| `Collapse` | `double` | get | `1 / Scale` (1 at scale 1). |
| `SurfaceBackdrop` | `Color` | get/set | Opaque colour the card erases to. |
| `SurfacePanOffset` | `Point` | get | Last pan handed over by the surface. |
| `SurfaceContentOffset` | `Offset` | get | Last world origin handed over by the surface. |
| `NodeTitle` | `Func<IWorkflowNodeViewModel, string>?` | get/set | How the view reads a node's title. |
| `SlotLabel` | `Func<IWorkflowSlotViewModel, string?>?` | get/set | How the view reads a slot's own label. |

**Methods**

| Method | Signature | Description |
|---|---|---|
| `ApplySurfacePosition` | `void ApplySurfacePosition(Point panOffset, Offset contentOffset)` | Stores the surface projection and re-places the card. |
| `ApplyPosition` | `void ApplyPosition()` | Places the card at `Anchor + pan + content`, resizes it to `Size`, and raises `CollapseChanged` / `Repositioned`. |
| `ResolveInputSlot` | `IWorkflowSlotViewModel? ResolveInputSlot()` | Finds the node's fixed input (source-only, non-target) slot. |
| `ResolveSlotLabel` | `string ResolveSlotLabel(IWorkflowSlotViewModel slot, int index)` | Enumerator name → `SlotLabel` → `"Output {n}"`. |

**Events**

| Event | Type | Raised when |
|---|---|---|
| `Repositioned` | `EventHandler?` | The card has been re-placed. |
| `Rebound` | `EventHandler?` | The node or its `Slots` collection changed. |
| `TitleChanged` | `EventHandler?` | The node title changed. |
| `CollapseChanged` | `EventHandler<CollapseChangedEventArgs>?` | The zoom collapse factor changed (`CollapseChangedEventArgs.Collapse`). |
| `Moving` / `Moved` | `EventHandler<NodeMoveEventArgs>?` | Before / after the node moves (`Moving` can `PreventDefault`). |
| `Resizing` / `Resized` | `EventHandler<NodeResizeEventArgs>?` | Before / after the node resizes (`Resizing` can `PreventDefault`). |
| `Deleting` / `Deleted` | `EventHandler<NodeEventArgs>?` | Before / after the node is removed (`Deleting` can `PreventDefault`). |
| `AnchorChanged` | `Action?` | Anchor or size changed after repositioning (the minimap repaints from this). |

### Class: `WorkflowSlotAttachment`

`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowSlotAttachment.cs`.

**Static methods**

| Method | Signature |
|---|---|
| `Attach` | `static WorkflowSlotAttachment Attach(Control target)` — throws `ArgumentNullException` for `null` |
| `For` | `static WorkflowSlotAttachment? For(Control target)` |
| `ParseColor` | `static Color ParseColor(string hex)` |
| `Opaque` | `static Color Opaque(Color color)` — forces alpha to 255 |

**Properties**

| Property | Type | Access | Description |
|---|---|---|---|
| `Slot` | `IWorkflowSlotViewModel?` | get/set | Bound slot; setting it rebinds events and visibility. |
| `SlotPath` | `string` | get/set | Glyph as an SVG path in the `PathViewBox` artboard. |
| `PathViewBox` | `float` | get/set | Artboard size (`1024` by default); non-positive values are ignored. |
| `SlotBackground` | `Color` | get/set | Fallback background when the control has no parent. |
| `StandbyColor` | `Color` | get/set | Glyph fill while idle. |
| `BorderColor` | `Color` | get/set | Glyph outline. |
| `IconPath` | `GraphicsPath?` | get | Parsed glyph, or `null` until `SlotPath` is set. |
| `GlyphColor` | `Color` | get | `Violet` for sender+receiver, `Tomato` sender, `Lime` receiver, else `StandbyColor`. |

**Methods**

| Method | Signature | Description |
|---|---|---|
| `Paint` | `void Paint(Graphics g)` | Draws `IconPath` scaled from `PathViewBox` into the control, using `GlyphColor` + `BorderColor`. Throws `ArgumentNullException` for a `null` `Graphics`. |

**Events**

| Event | Type | Raised when |
|---|---|---|
| `ChannelChanging` | `EventHandler<SlotChannelEventArgs>?` | Before the slot's channel changes (`PreventDefault` keeps it). |
| `ChannelChanged` | `EventHandler<SlotChannelEventArgs>?` | After the slot's channel changed. |

The constructor also calls `WorkflowSlotConnectionBehavior.SetIsEnabled(control, true)`, so an attached slot participates in the drag-to-connect gesture without extra wiring.

### Class: `WorkflowLinkAttachment`

`Src/Adapters/VeloxDev.WinForms/Attached/Workflow/WorkflowLinkAttachment.cs`.

**Static methods**

| Method | Signature |
|---|---|
| `Attach` | `static WorkflowLinkAttachment Attach(Control target)` — throws `ArgumentNullException` for `null` |
| `For` | `static WorkflowLinkAttachment? For(Control target)` |
| `ParseColor` | `static Color ParseColor(string hex)` |

**Properties**

| Property | Type | Access | Description |
|---|---|---|---|
| `Link` | `IWorkflowLinkViewModel?` | get | Currently bound link. |
| `Curve` | `PointF[]?` | get | The four Bézier points in control-local coordinates, or `null` when nothing is drawable. |
| `LineColor` | `Color` | get/set | Stroke colour. |
| `Thickness` | `float` | get/set | Stroke width; non-positive values are ignored and the window region is re-carved. |
| `PullMinimum` | `float` | get/set | Minimum horizontal control-point pull; negative values are ignored. |
| `SurfaceBackground` | `Color` | get/set | Colour behind the link; keep it equal to the surface grid background. |

**Methods**

| Method | Signature | Description |
|---|---|---|
| `Bind` | `void Bind(IWorkflowLinkViewModel? link)` | Binds/recycles the control: retracts the old curve, moves the input subscription, subscribes to the link and both endpoints, rebuilds geometry. |
| `Sync` | `void Sync(IWorkflowLinkViewModel? link)` | Re-reads `IsVisible` and rebuilds geometry. |
| `ApplySurfacePosition` | `void ApplySurfacePosition(Point panOffset, Offset contentOffset)` | Records the surface projection and rebuilds geometry. |
| `Paint` | `void Paint(Graphics g)` | Draws the resting cubic (dashed for a virtual link). Throws `ArgumentNullException` for a `null` `Graphics`. |

**Events** (forwarded from the link's `IInputEvents`)

| Event | Type |
|---|---|
| `PointerEntered` | `EventHandler<PointerEnteredEventArgs>?` |
| `PointerLeft` | `EventHandler<PointerExitedEventArgs>?` |
| `PointerPressed` | `EventHandler<PointerPressedEventArgs>?` |
| `PointerReleased` | `EventHandler<PointerReleasedEventArgs>?` |
| `KeyDown` / `KeyUp` | `EventHandler<KeyDownEventArgs>?` / `EventHandler<KeyUpEventArgs>?` |

The event args types live in `VeloxDev.WorkflowSystem`; the source file aliases that namespace as `Wf`.

`Attach` sets `Enabled = false` and `TabStop = false` and carves the control's window region to the stroke band, so the link does not swallow canvas gestures. `Bind` publishes the curve through `link.PublishCurve(...)` on every geometry rebuild, so hit testing and drawing share one curve.

## Interface: `IWorkflowTemplateSelector` (WinForms)

The attached-behaviors namespace's template-selector factory, declared in `Src/Adapters/VeloxDev.WinForms/Attached/Workflow/ViewManager.cs` and implemented by the generated `WorkflowTemplateSelector`. Jalium uses the platform `DataTemplateSelector` instead.

| Adapter | Member |
|---|---|
| WinForms | `Control CreateView(object item)` |

## Razor component helpers

Razor ships two small static helpers alongside the component behaviors, both in `VeloxDev.WorkflowSystem.AttachedBehaviors`:

### `WorkflowGeometryScope`

Suppresses per-node geometry writes during a zoom transaction so the atomic `applyZoomSurface` browser frame is the only geometry authority for the gesture.

| Member | Signature | Description |
|---|---|---|
| `IsZooming` | `static bool` | True while a zoom transaction is active on the current async flow. |
| `Zoom()` | `static IDisposable` | Enters a transaction; dispose the returned handle to leave it. |

Uses `AsyncLocal<int>` (never a plain static flag) so Blazor Server circuits sharing the process cannot observe each other's zoom.

### `WorkflowRuntimeIds`

Assigns stable, process-lifetime unique ids to workflow components by reference (weakly held), so Blazor elements can carry a `data-*-id` attribute that round-trips through JavaScript and resolves back to the same object.

| Member | Signature | Description |
|---|---|---|
| `Get` | `static string Get(object component)` | Stable id, assigning one on first use. |
| `TryFind` | `static bool TryFind<T>(string? id, out T? value) where T : class` | Resolves a component back from a previously assigned id. |
| `Enumerate` | `static IEnumerable<KeyValuePair<object, string>> Enumerate()` | All registered ids (diagnostics/tests). |

### `WorkflowPresentation`

Static CSS/geometry helpers for Razor views: `MinorGridColor`, `RulerBackground`, `RulerTickColor`, `RulerDividerColor`, `NodeForegroundCss` (CSS strings), `ToCss(string)`, and `InputSlotsOf(node)` / `OutputSlotsOf(node)` / `SlotNamesOf(node)` (channel-based slot split and labels).

### `SurfacePointerKind`

The browser-level pointer kinds the Razor surface accepts — `Entered`, `Moved`, `Exited`, `Pressed`, `Released`, `Wheel` — which `WorkflowSurfaceBehavior.RoutePointerAsync` maps to Core's `PointerEventArgs` before the shared input router sees them.
