# Platform Adapters - `MinimapOverlay.cs`

Exact output of `dotnet new wpf-v-minimap -n MinimapOverlay -ns Demo.Views.Workflow`. Subclasses the adapter `WorkflowMinimapOverlay` (in `VeloxDev.WorkflowSystem.AttachedBehaviors`) and applies the color symbols; drag/click navigation and offset pushes are inherited.

```csharp
using System.Windows.Media;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

namespace Demo.Views.Workflow;

/// <summary>
/// A minimap overlay that renders a thumbnail overview of a workflow surface.
/// Delegates data subscription and drag/click navigation to the canonical
/// <see cref="WorkflowMinimapOverlay"/> adapter (same data/logic as the full demo),
/// applying the template color symbols for the style.
/// </summary>
public class MinimapOverlay : WorkflowMinimapOverlay
{
    public MinimapOverlay()
    {
        MinimapBackground = CreateBrush("#D2141922");
        MinimapBorderBrush = CreateBrush("#DC94A3B8");
        NodeBrush = CreateBrush("#DC38BDF8");
        ViewportStroke = CreateBrush("#F0FFFFFF");
    }

    private static Brush CreateBrush(string hex)
        => new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
}
```
