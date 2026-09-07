# 平台适配器 - `MinimapOverlay.cs`

`dotnet new wpf-v-minimap -n MinimapOverlay -ns Demo.Views.Workflow` 的精确输出。继承适配器的 `WorkflowMinimapOverlay`（位于 `VeloxDev.WorkflowSystem.AttachedBehaviors`）并套用配色符号；拖拽/点击导航与偏移推送均继承自基类。

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
