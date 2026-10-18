# Platform Adapters - `LinkView.xaml / LinkView.xaml.cs`

Exact output of `dotnet new wpf-v-link -n LinkView -ns Demo.Views.Workflow` (template default colors substituted). A paint-only cubic Bézier connection that leaves each port horizontally and draws itself only when `CanRender` is true and the link reports render-ready (`IsRenderReady()`). It publishes the curve it draws for hit testing (`PublishCurve`, backed by the link's helper) and handles no input itself — hover feedback is the host's, driven through the tree's `IInputEvents`.

```xml
<!-- VeloxDev customization: Customize line geometry, color, thickness, hit testing, and virtual-link rendering in the code-behind. -->
<UserControl xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             x:Class="Demo.Views.Workflow.LinkView">
</UserControl>
```

```csharp
// VeloxDev customization: Customize line geometry, color, and thickness here.
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using VeloxDev.WorkflowSystem;

namespace Demo.Views.Workflow;

/// <summary>
/// Cubic Bézier connection that leaves each port horizontally.
/// The view only paints: it publishes its curve for hit-testing and handles no input itself. Hover feedback is
/// the host's — subscribe <c>IInputEvents</c> on the helper and handle the routed pointer events.
/// </summary>
public partial class LinkView : UserControl
{
    // Extension point: the least horizontal pull of the two control points. Keep it in step with the curve
    // that is published for hit-testing below.
    private const double MinimumPull = 40;

    // The link this view last published a curve to; retracted on rebind so a pooled view cannot leave a
    // stale curve answering for a link that no longer draws here.
    private IWorkflowLinkViewModel? _publishedLink;

    public LinkView()
    {
        InitializeComponent();
        IsHitTestVisible = false;
        Panel.SetZIndex(this, -100);

        DataContextChanged += OnDataContextChanged;
    }

    #region Dependency properties

    public static readonly DependencyProperty StartLeftProperty =
        DependencyProperty.Register(nameof(StartLeft), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnRenderChanged));
    public static readonly DependencyProperty StartTopProperty =
        DependencyProperty.Register(nameof(StartTop), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnRenderChanged));
    public static readonly DependencyProperty EndLeftProperty =
        DependencyProperty.Register(nameof(EndLeft), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnRenderChanged));
    public static readonly DependencyProperty EndTopProperty =
        DependencyProperty.Register(nameof(EndTop), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnRenderChanged));
    public static readonly DependencyProperty CanRenderProperty =
        DependencyProperty.Register(nameof(CanRender), typeof(bool), typeof(LinkView), new PropertyMetadata(true, OnRenderChanged));
    public static readonly DependencyProperty IsVirtualProperty =
        DependencyProperty.Register(nameof(IsVirtual), typeof(bool), typeof(LinkView), new PropertyMetadata(false, OnRenderChanged));
    public static readonly DependencyProperty LineColorProperty =
        DependencyProperty.Register(nameof(LineColor), typeof(Color), typeof(LinkView), new PropertyMetadata((Color)ColorConverter.ConvertFromString("#DDFFFFFF"), OnRenderChanged));

    public double StartLeft { get => (double)GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }
    public double StartTop { get => (double)GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }
    public double EndLeft { get => (double)GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }
    public double EndTop { get => (double)GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }
    public bool CanRender { get => (bool)GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }
    public bool IsVirtual { get => (bool)GetValue(IsVirtualProperty); set => SetValue(IsVirtualProperty, value); }
    public Color LineColor { get => (Color)GetValue(LineColorProperty); set => SetValue(LineColorProperty, value); }

    private static void OnRenderChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        => ((LinkView)d).InvalidateVisual();

    private void OnDataContextChanged(object? sender, DependencyPropertyChangedEventArgs e)
    {
        // Retract the previous link's curve, then let the next draw publish the new one.
        _publishedLink?.PublishCurve(null);
        _publishedLink = null;
        InvalidateVisual();
    }

    private bool IsVirtualLink
        => IsVirtual
            || DataContext is IWorkflowLinkViewModel
            {
                Sender.Parent: null,
                Receiver.Parent: null
            };

    #endregion

    #region Render

    protected override void OnRender(DrawingContext ctx)
    {
        base.OnRender(ctx);
        if (!CanRender) return;
        if (DataContext is IWorkflowLinkViewModel link && !link.IsRenderReady()) return;

        // Publish the curve the surface hit-tests against: same control points as BuildCurve, same
        // canvas-local space. Replace this together with BuildCurve if you change the shape.
        PublishCurve(LinkCurve.BuildLinkCubic(DataContext as IWorkflowLinkViewModel, StartLeft, StartTop, EndLeft, EndTop, MinimumPull));

        var thickness = 2;
        var geometry = BuildCurve(DataContext as IWorkflowLinkViewModel);

        var brush = new SolidColorBrush(LineColor);
        var pen = IsVirtualLink
            ? new Pen(brush, thickness) { DashStyle = new DashStyle(new double[] { 4, 2 }, 0) }
            : new Pen(brush, thickness);

        ctx.DrawGeometry(null, pen, geometry);
    }

    // Extension point: the control points set the curve's shape. Core derives them from each port's own edge
    // (LinkCurve.LinkCurvePoints) — keep that source if you replace the drawing.
    private Geometry BuildCurve(IWorkflowLinkViewModel? link)
    {
        var points = LinkCurve.LinkCurvePoints(link, StartLeft, StartTop, EndLeft, EndTop, MinimumPull);
        var figure = new PathFigure
        {
            StartPoint = new Point(points[0].X, points[0].Y),
            IsClosed = false,
            IsFilled = false,
        };
        figure.Segments.Add(new BezierSegment(
            new Point(points[1].X, points[1].Y),
            new Point(points[2].X, points[2].Y),
            new Point(points[3].X, points[3].Y),
            true));

        var geometry = new PathGeometry();
        geometry.Figures.Add(figure);
        geometry.Freeze();
        return geometry;
    }

    // Extension point: change the second argument if one view no longer draws exactly one link.
    private void PublishCurve(LinkCurve curve)
    {
        var link = DataContext as IWorkflowLinkViewModel;
        if (!ReferenceEquals(_publishedLink, link))
        {
            _publishedLink?.PublishCurve(null);
            _publishedLink = link;
        }

        if (link is not null)
        {
            link.PublishCurve(curve, this);
        }
    }

    #endregion
}
```
