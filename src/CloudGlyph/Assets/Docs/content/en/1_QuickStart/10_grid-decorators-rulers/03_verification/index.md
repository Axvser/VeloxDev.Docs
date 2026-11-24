# Verification

This sample adds a compact `GridRulerDecorator` to the view-hosting host. It draws the canvas grid below the content and the floating rulers above it, and implements `IWorkflowGridDecorator` so the surface keeps it aligned.

## Run the reference

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

## Check each behaviour

1. **Grid alignment.** Pan the canvas: vertical and horizontal lines move by exactly the scroll delta and never drift.
2. **World origin.** The two lines at world `0` are brighter than the rest.
3. **Major lines.** Every fifth line (200 canvas units at the default spacing) is stronger and carries a label.
4. **Rulers.** The top and left bands stay fixed while the content scrolls under them. Labels show grid coordinates.
5. **Zoom.** Zoom with `Ctrl` + wheel: the grid keeps its pixel spacing; it does not scale with the node cards.
6. **Ruler inset.** Drag a node under the ruler band. It remains visible; it is not culled one band too early.
7. **Minimap.** If you also attach the minimap, its top edge sits below the ruler band.

The Razor headless suite renders the decorator and asserts the rulers are produced (`GridDecoratorTests`); the WPF headless suite asserts the surface pushes offsets to the named decorator (`Scroll_PushesOffsetsToTheGridDecorator`).

## Complete code

### `Views/Workflow/GridRulerDecorator.cs`

```csharp
using System;
using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using VeloxDev.WorkflowSystem;

namespace Demo;

public sealed class GridRulerDecorator : Grid, IWorkflowGridDecorator
{
    private const double Epsilon = 0.001;
    private static readonly Brush SurfaceBrush = new SolidColorBrush(Color.Parse("#171717"));
    private static readonly Brush RulerBrush = new SolidColorBrush(Color.FromArgb(0xD2, 0x1F, 0x1F, 0x1F));
    private static readonly Brush LabelBrush = new SolidColorBrush(Color.Parse("#6E7681"));
    private static readonly Pen MinorPen = new(new SolidColorBrush(Color.Parse("#232323")), 1);
    private static readonly Pen MajorPen = new(new SolidColorBrush(Color.Parse("#2E2E2E")), 1);
    private static readonly Pen AxisPen = new(new SolidColorBrush(Color.Parse("#3A3A3A")), 1.2);
    private static readonly Pen TickPen = new(new SolidColorBrush(Color.Parse("#4A4A4A")), 1);
    private static readonly Pen DividerPen = new(new SolidColorBrush(Color.Parse("#2E2E2E")), 1);
    private static readonly Typeface Face = new(
        new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);

    private readonly GridLayer grid;
    private readonly RulerLayer ruler;

    public static readonly DependencyProperty RulerThicknessProperty = DependencyProperty.Register(
        nameof(RulerThickness), typeof(double), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(28d, OnVisualChanged));
    public static readonly DependencyProperty GridSpacingProperty = DependencyProperty.Register(
        nameof(GridSpacing), typeof(double), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(40d, OnVisualChanged));
    public static readonly DependencyProperty MajorLineEveryProperty = DependencyProperty.Register(
        nameof(MajorLineEvery), typeof(int), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(5, OnVisualChanged));
    public static readonly DependencyProperty ScrollOffsetXProperty = DependencyProperty.Register(
        nameof(ScrollOffsetX), typeof(double), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(0d, OnVisualChanged));
    public static readonly DependencyProperty ScrollOffsetYProperty = DependencyProperty.Register(
        nameof(ScrollOffsetY), typeof(double), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(0d, OnVisualChanged));
    public static readonly DependencyProperty ContentOffsetXProperty = DependencyProperty.Register(
        nameof(ContentOffsetX), typeof(double), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(0d, OnVisualChanged));
    public static readonly DependencyProperty ContentOffsetYProperty = DependencyProperty.Register(
        nameof(ContentOffsetY), typeof(double), typeof(GridRulerDecorator), new FrameworkPropertyMetadata(0d, OnVisualChanged));

    public GridRulerDecorator()
    {
        ClipToBounds = true;
        grid = new GridLayer(this) { IsHitTestVisible = false };
        ruler = new RulerLayer(this) { IsHitTestVisible = false };
        Panel.SetZIndex(ruler, 100);
        Children.Add(grid);
        Children.Add(ruler);
        SizeChanged += (_, _) => Invalidate();
    }

    public double RulerThickness { get => (double)GetValue(RulerThicknessProperty); set => SetValue(RulerThicknessProperty, value); }
    public double GridSpacing { get => (double)GetValue(GridSpacingProperty); set => SetValue(GridSpacingProperty, value); }
    public int MajorLineEvery { get => (int)GetValue(MajorLineEveryProperty); set => SetValue(MajorLineEveryProperty, value); }
    public double ScrollOffsetX { get => (double)GetValue(ScrollOffsetXProperty); set => SetValue(ScrollOffsetXProperty, value); }
    public double ScrollOffsetY { get => (double)GetValue(ScrollOffsetYProperty); set => SetValue(ScrollOffsetYProperty, value); }
    public double ContentOffsetX { get => (double)GetValue(ContentOffsetXProperty); set => SetValue(ContentOffsetXProperty, value); }
    public double ContentOffsetY { get => (double)GetValue(ContentOffsetYProperty); set => SetValue(ContentOffsetYProperty, value); }
    public double RulerBand => RulerThickness;

    private static void OnVisualChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        => ((GridRulerDecorator)d).Invalidate();

    private void Invalidate()
    {
        grid.InvalidateVisual();
        ruler.InvalidateVisual();
    }

    private static Pen PenFor(double value, double majorStep)
        => IsNearZero(value) ? AxisPen : IsMajorLine(value, majorStep) ? MajorPen : MinorPen;

    private static bool IsMajorLine(double value, double majorStep)
    {
        if (majorStep <= 0) return false;
        var remainder = value % majorStep;
        return Math.Abs(remainder) < Epsilon
            || Math.Abs(remainder - majorStep) < Epsilon
            || Math.Abs(remainder + majorStep) < Epsilon;
    }

    private static bool IsNearZero(double value) => Math.Abs(value) < Epsilon;

    private static void DrawLabel(DrawingContext dc, double value, Point origin)
        => dc.DrawText(new FormattedText(
            Math.Round(value).ToString(CultureInfo.InvariantCulture),
            CultureInfo.InvariantCulture, FlowDirection.LeftToRight, Face, 10, LabelBrush, 1.0), origin);

    private sealed class GridLayer(GridRulerDecorator owner) : FrameworkElement
    {
        protected override Size MeasureOverride(Size availableSize) => availableSize;

        protected override void OnRender(DrawingContext dc)
        {
            var b = new Rect(RenderSize);
            if (b.Width <= 0 || b.Height <= 0) return;
            dc.DrawRectangle(SurfaceBrush, null, b);

            var band = Math.Max(0, owner.RulerThickness);
            var step = Math.Max(8, owner.GridSpacing);
            var major = step * Math.Max(1, owner.MajorLineEvery);
            var left = WorkflowSurfaceMath.GridCanvasLeft(owner.ScrollOffsetX, owner.ContentOffsetX);
            var top = WorkflowSurfaceMath.GridCanvasTop(owner.ScrollOffsetY, owner.ContentOffsetY);

            for (var v = WorkflowSurfaceMath.GridFirstLine(left, step); v <= left + b.Width + step; v += step)
            {
                var x = WorkflowSurfaceMath.GridX(v, left, band);
                dc.DrawLine(PenFor(v, major), new Point(x, 0), new Point(x, b.Height));
            }

            for (var v = WorkflowSurfaceMath.GridFirstLine(top, step); v <= top + b.Height + step; v += step)
            {
                var y = WorkflowSurfaceMath.GridY(v, top, band);
                dc.DrawLine(PenFor(v, major), new Point(0, y), new Point(b.Width, y));
            }
        }
    }

    private sealed class RulerLayer(GridRulerDecorator owner) : FrameworkElement
    {
        protected override Size MeasureOverride(Size availableSize) => availableSize;

        protected override void OnRender(DrawingContext dc)
        {
            var b = new Rect(RenderSize);
            if (b.Width <= 0 || b.Height <= 0) return;

            var band = Math.Max(0, owner.RulerThickness);
            dc.DrawRectangle(RulerBrush, null, new Rect(0, 0, b.Width, band));
            dc.DrawRectangle(RulerBrush, null, new Rect(0, 0, band, b.Height));
            dc.DrawLine(DividerPen, new Point(band, 0), new Point(band, b.Height));
            dc.DrawLine(DividerPen, new Point(0, band), new Point(b.Width, band));

            var step = Math.Max(8, owner.GridSpacing);
            var major = step * Math.Max(1, owner.MajorLineEvery);
            var left = WorkflowSurfaceMath.GridCanvasLeft(owner.ScrollOffsetX, owner.ContentOffsetX);
            var top = WorkflowSurfaceMath.GridCanvasTop(owner.ScrollOffsetY, owner.ContentOffsetY);

            for (var v = WorkflowSurfaceMath.GridFirstLine(left, step); v <= left + b.Width + step; v += step)
            {
                var x = WorkflowSurfaceMath.GridX(v, left, band);
                if (x < band) continue;

                var isMajor = IsMajorLine(v, major);
                var tick = isMajor ? band - 6 : Math.Max(6, band * 0.35);
                dc.DrawLine(IsNearZero(v) ? AxisPen : TickPen, new Point(x, band), new Point(x, band - tick));
                if (isMajor) DrawLabel(dc, v, new Point(x + 3, 2));
            }

            for (var v = WorkflowSurfaceMath.GridFirstLine(top, step); v <= top + b.Height + step; v += step)
            {
                var y = WorkflowSurfaceMath.GridY(v, top, band);
                if (y < band) continue;

                var isMajor = IsMajorLine(v, major);
                var tick = isMajor ? band - 6 : Math.Max(6, band * 0.35);
                dc.DrawLine(IsNearZero(v) ? AxisPen : TickPen, new Point(band, y), new Point(band - tick, y));
                if (isMajor) DrawLabel(dc, v, new Point(3, y + 2));
            }
        }
    }
}
```

### `Views/Workflow/TreeView.xaml`

The view models and the `WorkflowTemplateSelector` class are the ones on [View hosting and virtualization](../../08_view-hosting-virtualization/03_verification/index.md).

```xml
<UserControl x:Class="Demo.TreeView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:Demo"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator">
    <UserControl.Resources>
        <BooleanToVisibilityConverter x:Key="BoolToVisibility" />

        <DataTemplate x:Key="NodeTemplate">
            <Border Width="{Binding Size.Width}" Height="{Binding Size.Height}"
                    Background="#DD2D2D30" CornerRadius="6"
                    Canvas.Left="{Binding Anchor.Horizontal}"
                    Canvas.Top="{Binding Anchor.Vertical}"
                    Panel.ZIndex="{Binding Anchor.Layer}"
                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:TreeView}},
                                              Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}">
                <TextBlock Text="{Binding Name}" Foreground="#DDE7E7E7" Margin="12" />
            </Border>
        </DataTemplate>

        <DataTemplate x:Key="LinkTemplate">
            <Canvas Width="{Binding RelativeSource={RelativeSource AncestorType={x:Type Canvas}}, Path=ActualWidth}"
                    Height="{Binding RelativeSource={RelativeSource AncestorType={x:Type Canvas}}, Path=ActualHeight}"
                    IsHitTestVisible="False"
                    Visibility="{Binding IsVisible, Converter={StaticResource BoolToVisibility}}">
                <Line X1="{Binding Sender.Anchor.Horizontal}" Y1="{Binding Sender.Anchor.Vertical}"
                      X2="{Binding Receiver.Anchor.Horizontal}" Y2="{Binding Receiver.Anchor.Vertical}"
                      Stroke="#CC6E8BFF" StrokeThickness="2" />
            </Canvas>
        </DataTemplate>

        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}"
                                        LinkTemplate="{StaticResource LinkTemplate}" />
    </UserControl.Resources>

    <Border x:Name="PART_SurfaceBorder" Background="#171717">
        <local:GridRulerDecorator x:Name="PART_GridDecorator">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}"
                        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}">
                    <Canvas.RenderTransform>
                        <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                            Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                    </Canvas.RenderTransform>
                </Canvas>
            </ScrollViewer>
        </local:GridRulerDecorator>
    </Border>
</UserControl>
```

## Run declaration

⚠️ Not actually run — statically verified only. The decorator implements the interface and the four formulas exactly as `WorkflowSurfaceMath` defines them; the grid template this sample is based on is `Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-grid-decorator/TemplateClass.cs`. The surface-push path is asserted by `Scroll_PushesOffsetsToTheGridDecorator` and `SurfaceMetricsPush_PushGrid_WritesOffsets`. No window was launched while writing this page.
