# 平台适配器 — `MinimapOverlay.cs`

Source file from the complete scaffold.

```csharp

// ====================== MinimapOverlay.cs ======================

using System.Windows.Media;

using VeloxDev.WorkflowSystem.AttachedBehaviors;



namespace Demo.Views.Workflow;



public sealed class MinimapOverlay : WorkflowMinimapOverlay

{

    public MinimapOverlay()

    {

        MinimapBackground = CreateBrush("#141922");

        MinimapBorderBrush = CreateBrush("#31445C");

        NodeBrush = CreateBrush("#38BDF8");

        ViewportStroke = CreateBrush("#FFFFFF");

    }



    private static Brush CreateBrush(string hex)

        => new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));

}

```
