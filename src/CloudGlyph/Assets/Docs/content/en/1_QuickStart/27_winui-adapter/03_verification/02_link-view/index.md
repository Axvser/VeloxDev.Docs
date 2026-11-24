# Link View

This is the offset-frame link control referenced by `LinkTemplate` on the previous page. It publishes the raw canvas-local curve for hit-testing and draws the same curve with the canvas pan baked in, so the geometry always lands inside the element's own box.

```csharp
using System.ComponentModel;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Shapes;
using VeloxDev.WorkflowSystem;
using Windows.Foundation;
using Path = Microsoft.UI.Xaml.Shapes.Path;

namespace MyApp;

public sealed class LinkView : UserControl
{
    private const double PullMinimum = 40;

    private readonly Path _path = new()
    {
        Stroke = new SolidColorBrush(Microsoft.UI.Colors.WhiteSmoke),
        StrokeThickness = 2,
        StrokeLineJoin = PenLineJoin.Round,
        IsHitTestVisible = false,
        Clip = null
    };

    private CanvasLayout? _layout;
    private PropertyChangedEventHandler? _layoutHandler;
    private ILinkComponent? _boundLink;

    public LinkView()
    {
        IsHitTestVisible = false;
        Clip = null;
        Content = new Grid { Clip = null, Children = { _path } };

        Loaded += OnLoaded;
        Unloaded += OnUnloaded;
        DataContextChanged += OnDataContextChanged;
    }

    public static readonly DependencyProperty StartLeftProperty = DependencyProperty.Register(
        nameof(StartLeft), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnChanged));
    public static readonly DependencyProperty StartTopProperty = DependencyProperty.Register(
        nameof(StartTop), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnChanged));
    public static readonly DependencyProperty EndLeftProperty = DependencyProperty.Register(
        nameof(EndLeft), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnChanged));
    public static readonly DependencyProperty EndTopProperty = DependencyProperty.Register(
        nameof(EndTop), typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnChanged));
    public static readonly DependencyProperty CanRenderProperty = DependencyProperty.Register(
        nameof(CanRender), typeof(bool), typeof(LinkView), new PropertyMetadata(true, OnChanged));

    public double StartLeft { get => (double)GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }
    public double StartTop { get => (double)GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }
    public double EndLeft { get => (double)GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }
    public double EndTop { get => (double)GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }
    public bool CanRender { get => (bool)GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }

    private static void OnChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        => ((LinkView)d).UpdatePath();

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        UpdateLayoutSubscription();
        UpdatePath();
    }

    private void OnUnloaded(object sender, RoutedEventArgs e) => UnsubscribeLayout();

    private void OnDataContextChanged(FrameworkElement sender, DataContextChangedEventArgs args)
    {
        if (!ReferenceEquals(_boundLink, args.NewValue as ILinkComponent))
        {
            _boundLink?.PublishCurve(null);
            _boundLink = args.NewValue as ILinkComponent;
        }

        UpdateLayoutSubscription();
        UpdatePath();
    }

    private void UpdateLayoutSubscription()
    {
        UnsubscribeLayout();
        if (DataContext is not ILinkComponent link) return;

        var tree = link.Sender?.Parent?.Parent as ITreeComponent
                   ?? link.Receiver?.Parent?.Parent as ITreeComponent
                   ?? FindHostTree();
        if (tree?.Layout is not { } layout) return;

        _layout = layout;
        _layoutHandler = OnLayoutPropertyChanged;
        layout.PropertyChanged += _layoutHandler;
    }

    private ITreeComponent? FindHostTree()
    {
        for (var p = Parent as FrameworkElement; p is not null; p = p.Parent as FrameworkElement)
        {
            if (p.DataContext is ITreeComponent tree) return tree;
        }

        return null;
    }

    private void UnsubscribeLayout()
    {
        if (_layout is not null && _layoutHandler is not null) _layout.PropertyChanged -= _layoutHandler;
        _layout = null;
        _layoutHandler = null;
    }

    private void OnLayoutPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName is nameof(CanvasLayout.ActualOffset) or nameof(CanvasLayout.ActualSize))
        {
            UpdatePath();
        }
    }

    private void UpdatePath()
    {
        if (!CanRender) { _path.Data = null; return; }
        if (DataContext is ILinkComponent link && !link.IsRenderReady()) { _path.Data = null; return; }

        var ox = _layout?.ActualOffset.Horizontal ?? 0d;
        var oy = _layout?.ActualOffset.Vertical ?? 0d;
        Canvas.SetLeft(this, -ox);
        Canvas.SetTop(this, -oy);
        Width = _layout?.ActualSize.Width ?? 0d;
        Height = _layout?.ActualSize.Height ?? 0d;

        var curve = LinkCurve.BuildLinkCubic(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        if (DataContext is ILinkComponent bound) bound.PublishCurve(curve, this);

        var p = LinkCurve.LinkCurvePoints(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        var geometry = new PathGeometry();
        var figure = new PathFigure
        {
            StartPoint = new Point(p[0].X + ox, p[0].Y + oy),
            IsClosed = false
        };
        figure.Segments.Add(new BezierSegment
        {
            Point1 = new Point(p[1].X + ox, p[1].Y + oy),
            Point2 = new Point(p[2].X + ox, p[2].Y + oy),
            Point3 = new Point(p[3].X + ox, p[3].Y + oy)
        });
        geometry.Figures.Add(figure);
        _path.Data = geometry;
    }
}
```

`PublishCurve` receives the **un-baked** curve: the coordinates are the raw `Sender.Anchor` / `Receiver.Anchor` values, which is the same frame the surface queries. The `+ox/+oy` is only for the retained `Path` geometry, and `-ox/-oy` is only the element's placement.

**Expected result:** the link stays aligned with both ports at any zoom, and neither the element nor the path clips at deep zoom.

## Run Declaration

- ⚠️ Not actually run — statically verified only. The offset-frame construction, `Path`/`PathGeometry`/`BezierSegment` usage, `CanvasLayout.ActualOffset` / `ActualSize` names and the attached properties were checked against `Src/Adapters/VeloxDev.WinUI/`, `Src/Core/VeloxDev.Core/` and `Examples/Workflow/WinUI Trimmed/Demo/Views/Workflow/LinkView.xaml.cs`. The file set was not compiled or executed in the writing session.
