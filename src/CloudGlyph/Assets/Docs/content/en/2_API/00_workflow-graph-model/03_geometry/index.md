# Geometry models

The geometry value types are mutable view models (except `Viewport` and `WorkflowBounds`, which are readonly structs). `Anchor` and `Size` store **world** values; their getters return a view value collapsed by `CanvasLayout.Scale`.

Namespace: `VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## Anchor

**Signature:** `sealed partial class Anchor(double left = 0d, double top = 0d, int layer = 0) : ICloneable, IEquatable<Anchor>`

| Member | Type | Description |
| --- | --- | --- |
| `Horizontal` | `double` | Left coordinate. |
| `Vertical` | `double` | Top coordinate. |
| `Layer` | `int` | Draw layer; interpreted by the adapter. |
| `Collapse(Scale?)` | `Anchor` | View value toward the world origin (`value / scale`); identity for null or 1. |
| `Expand(Scale?)` | `Anchor` | World value from a view value (`view * scale`); inverse of `Collapse`. |
| `Clone()` / `Equals(...)` / `GetHashCode()` / `ToString()` | | Value semantics; `ToString` is `Anchor(x,y,layer)`. |
| `operator +`, `operator -` | `Anchor` | Component-wise, including `Layer`. |
| `operator ==`, `operator !=` | `bool` | Value equality. |

The collapsed instance remembers its scale and owner internally so serialization writes world coordinates; do not mutate the object returned by a node's `Anchor` getter — assign through the property instead.

## Size

**Signature:** `sealed partial class Size(double width = 0d, double height = 0d) : ICloneable, IEquatable<Size>`

Members: `Width`, `Height`; `Collapse(Scale?)`, `Expand(Scale?)`; `Clone()`, `Equals`, `GetHashCode`, `ToString` (`Size(w,h)`); `+`, `-`, `==`, `!=`.

## Offset

**Signature:** `sealed partial class Offset(double left = 0d, double top = 0d) : ICloneable, IEquatable<Offset>`

Members: `Horizontal`, `Vertical`; `Clone()`, `Equals`, `GetHashCode`, `ToString` (`Offset(x,y)`); `+`, `-`, `==`, `!=`. An `Offset` is a delta: the node move command interprets it in view space.

## Scale

**Signature:** `sealed partial class Scale(double horizontal = 1d, double vertical = 1d) : ICloneable, IEquatable<Scale>`

Members: `Horizontal`, `Vertical`; `Clone()`, `Equals`, `GetHashCode`, `ToString` (`Scale(x,y)`); `+`, `-`, `==`, `!=`. `1.0` means no scaling.

## ZoomCenter

**Signature:** `enum ZoomCenter`

| Value | Description |
| --- | --- |
| `WorldOrigin = 0` | Collapse toward the world origin; a viewport far from `(0,0)` can lose its nodes. |
| `ViewportCenter = 1` | Collapse about the world point at the viewport centre; the visible content stays put. |

The canvas geometry is the same in both modes; `ViewportCenter` scrolls the pivot under the viewport centre instead of moving the canvas.

## CanvasLayout

**Signature:** `sealed partial class CanvasLayout : ICloneable, IEquatable<CanvasLayout>`

| Member | Type | Default | Description |
| --- | --- | --- | --- |
| `OriginSize` | `Size` | `1920×1080` | Base canvas extent. |
| `PositiveOffset` | `Offset` | `0,0` | Extra extent on the positive side. |
| `NegativeOffset` | `Offset` | `0,0` | Extra extent on the negative side. |
| `Scale` | `Scale` | `1,1` | Zoom applied to every node view. |
| `ActualSize` | `Size` | computed | Scrollable extent; grows by `1/Scale` while zoomed in (`Scale < 1`). |
| `ActualOffset` | `Offset` | computed | Equal to `NegativeOffset`. |
| `ViewportOffset` | `Offset` | `0,0` | Current scroll position. |
| `ZoomCenter` | `ZoomCenter` | `ViewportCenter` | Collapse mode. |
| `CollapsePivot` | `Anchor` | `0,0,0` | Pivot written by an adapter immediately before a scale change. |
| `UpdateCommand` | `IVeloxCommand` | — | Recomputes `ActualSize`/`ActualOffset`; no parameter. |

Methods: `AdaptTo(Size targetOriginSize, out double suggestedViewportX, out double suggestedViewportY)` returns a copy adapted to a new origin size and computes a centring viewport position; `AdaptTo(Size)` is the same without the out values. `Clone()`, `Equals(CanvasLayout?)` and `GetHashCode()` cover the geometry and zoom settings.

Changing `OriginSize`, `PositiveOffset`, `NegativeOffset` or `Scale` recomputes `ActualSize`/`ActualOffset` and re-raises `ActualSize`. Changing `CollapsePivot` or `ZoomCenter` alone does not resize the canvas.

## Viewport

**Signature:** `readonly struct Viewport(double left, double top, double width, double height) : IEquatable<Viewport>, ISampleable`

| Member | Type | Description |
| --- | --- | --- |
| `Empty` | `Viewport` | Zero-sized viewport (`default`). |
| `Horizontal` / `Vertical` | `double` | Left / top edge. |
| `Width` / `Height` | `double` | Extent. |
| `Right` / `Bottom` | `double` | Far edges. |
| `IsEmpty` | `bool` | True when the width or the height is zero or less. |
| `IntersectsWith(double left, double top, double width, double height)` | `bool` | Rectangle intersection. |
| `IntersectsWith(Viewport)` | `bool` | Viewport intersection. |
| `Contains(double x, double y)` / `Contains(Viewport)` | `bool` | Point or full containment. |
| `Union(Viewport a, Viewport b)` | `Viewport` | Minimal covering viewport. |
| `GetAnimatableMembers()` / `CreateFrameValue(...)` | `ISampleable` | Animation support: members are left, top, width, height. |

## WorkflowBounds

**Signature:** `readonly struct WorkflowBounds`

| Member | Type | Description |
| --- | --- | --- |
| `Left` / `Top` / `Width` / `Height` | `double` | Init-only edges and extent. |
| `Right` / `Bottom` | `double` | Far edges. |
| `IsEmpty` | `bool` | No area. |
| `FromNode(double x, double y, double w, double h)` | `WorkflowBounds` | One node rectangle. |
| `FromNodes(IEnumerable<(double X, double Y, double W, double H)>)` | `WorkflowBounds` | Union of rectangles. |
| `Union(WorkflowBounds a, WorkflowBounds b)` | `WorkflowBounds` | Minimal covering bounds. |

`WorkflowBounds` is also the bounds type reported by the layout cost measure; see [Layout solution](../../06_workflow-auto-layout/02_layout-solution/index.md).

## Example

```csharp
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 2), Size = new Size(220, 120) };
var tree = new TreeDefaultViewModel();
tree.GetHelper().CreateNode(node);

tree.Layout.Scale = new Scale(0.5, 0.5);
Console.WriteLine(node.Anchor);            // Anchor(120,160,2): collapsed view value
Console.WriteLine(node.GetWorldAnchor());  // Anchor(60,80,2): stored world value
Console.WriteLine(tree.Layout.ActualSize); // 3840x2160 at Scale 0.5
```
