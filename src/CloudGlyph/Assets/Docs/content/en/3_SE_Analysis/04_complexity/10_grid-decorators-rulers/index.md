# Grid decorators and rulers

The grid is drawn as line strips, not as per-cell rectangles. That changes the asymptotic cost: a viewport of $c$ cells needs only one vertical line per column and one horizontal line per row, so the cost is proportional to the square root of the cell count. The ruler reuses the same spacing and the same loop bounds, adding a label only on major ticks.

Notation: $W$ and $H$ viewport size, $s$ grid spacing, $m$ `MajorLineEvery`, $c_w = W/s$ columns, $c_h = H/s$ rows, $c = c_w c_h$ visible cells.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| Grid layer render | $O(c_w + c_h)$ | $O(c_w + c_h)$ draw calls | `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:161` |
| Ruler layer render | $O(c_w + c_h) + O((c_w + c_h)/m)$ labels | $O(c_w + c_h)$ ticks | `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:194` |
| Full repaint | twice $O(c_w + c_h)$ | — | both layers invalidated together |
| `IsMajorLine` | $O(1)$ | — | `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:275` |
| Offset mapping | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:187` |
| First visible line | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:216` |
| Razor tick window rebuild | $O(3(c_w + c_h))$ per rebuild | $O(c_w + c_h)$ DOM nodes | `Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/WorkflowGridDecorator.razor.cs:180` |

## One line per column, one per row

The grid loops increment by the spacing and draw a full-length line at each step:

```csharp
var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    var pen = IsNearZero(value) ? AxisPen : IsMajorLine(value, majorStep) ? MajorGridPen : MinorGridPen;
    context.DrawLine(pen, new Point(x, 0), new Point(x, bounds.Height));
}
```

Source: `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:171-177`

The horizontal loop is the mirror image. With defaults $s = 40$ and $m = 5$, a major line appears every 200 world units. The bound is:

$$
T_{\text{grid}}(W,H) = O\!\left(\frac{W}{s} + \frac{H}{s}\right) = O(c_w + c_h)
$$

not $O(c)$. A per-cell design would draw $c_w c_h$ rectangles and be quadratic in viewport size.

```plot
{
  "title": "Grid cost: line strips vs per-cell rectangles",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 2500] },
  "data": [
    { "fn": "2*x", "color": "#4a9eff", "title": "O(W/s + H/s), line strips" },
    { "fn": "x*x", "color": "#f472b6", "title": "O(c), per-cell rectangles" }
  ]
}
```

## Rulers reuse the loop

The ruler layer iterates the same values, skips anything inside the band, and draws a tick whose length depends on whether the value is major:

```csharp
var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldRight + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    if (x < ruler) { continue; }
    var isMajor = IsMajorLine(value, majorStep);
    var tickLength = isMajor ? ruler - 6 : Math.Max(6, ruler * 0.35);
```

Source: `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowGridDecorator.cs:217-227`

A label is formatted only on major ticks, so label cost is $O((c_w + c_h)/m)$. Both layers are invalidated together on any offset or spacing change, which is why a full repaint is twice the per-layer bound.

## Offset math is constant-time

The world-to-local mapping is arithmetic; the only non-trivial part is starting at the first line at or below the visible edge:

```csharp
public static double GridCanvasLeft(double scrollOffset, double contentOffset) => scrollOffset - contentOffset;
...
public static double GridFirstLine(double localLeft, double spacing) => Math.Floor(localLeft / spacing) * spacing;
```

Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:187-217`

Scrolling changes only the phase of the loops, not their iteration count, so a scroll frame costs the same as any other grid frame.

## Space and the Razor variant

The WPF-style implementation keeps no collection: its space is the retained draw calls and formatted labels until the next render. The Razor adapter cannot use immediate-mode drawing, so it materializes tick nodes in a window three viewports wide and rebuilds only when the visible range leaves the inner half-margin. That converts an unbounded DOM into $O(3(c_w + c_h))$ nodes, amortized to one rebuild per viewport of pan; per-frame CSS translation is $O(1)$.
