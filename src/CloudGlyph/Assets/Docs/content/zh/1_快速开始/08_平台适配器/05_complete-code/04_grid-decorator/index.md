# 平台适配器 — `GridDecorator.cs`

Source file from the complete scaffold.

```csharp

// ====================== GridDecorator.cs ======================

using System;

using System.Windows;

using System.Windows.Controls;

using System.Windows.Media;

using VeloxDev.WorkflowSystem.AttachedBehaviors;



namespace Demo.Views.Workflow;



public sealed class GridDecorator : Decorator, IWorkflowGridDecorator

{

    private static readonly Pen MinorPen = CreatePen("#223043", 1);

    private static readonly Pen MajorPen = CreatePen("#31445C", 1);



    public static readonly DependencyProperty ScrollOffsetXProperty = RegisterOffset(nameof(ScrollOffsetX));

    public static readonly DependencyProperty ScrollOffsetYProperty = RegisterOffset(nameof(ScrollOffsetY));

    public static readonly DependencyProperty ContentOffsetXProperty = RegisterOffset(nameof(ContentOffsetX));

    public static readonly DependencyProperty ContentOffsetYProperty = RegisterOffset(nameof(ContentOffsetY));

    public static readonly DependencyProperty GridSpacingProperty =

        DependencyProperty.Register(nameof(GridSpacing), typeof(double), typeof(GridDecorator),

            new FrameworkPropertyMetadata(40d, FrameworkPropertyMetadataOptions.AffectsRender));

    public static readonly DependencyProperty MajorLineEveryProperty =

        DependencyProperty.Register(nameof(MajorLineEvery), typeof(int), typeof(GridDecorator),

            new FrameworkPropertyMetadata(5, FrameworkPropertyMetadataOptions.AffectsRender));



    public double ScrollOffsetX { get => (double)GetValue(ScrollOffsetXProperty); set => SetValue(ScrollOffsetXProperty, value); }

    public double ScrollOffsetY { get => (double)GetValue(ScrollOffsetYProperty); set => SetValue(ScrollOffsetYProperty, value); }

    public double ContentOffsetX { get => (double)GetValue(ContentOffsetXProperty); set => SetValue(ContentOffsetXProperty, value); }

    public double ContentOffsetY { get => (double)GetValue(ContentOffsetYProperty); set => SetValue(ContentOffsetYProperty, value); }

    public double GridSpacing { get => (double)GetValue(GridSpacingProperty); set => SetValue(GridSpacingProperty, value); }

    public int MajorLineEvery { get => (int)GetValue(MajorLineEveryProperty); set => SetValue(MajorLineEveryProperty, value); }



    public GridDecorator()

    {

        ClipToBounds = true;

        SnapsToDevicePixels = true;

    }



    private static DependencyProperty RegisterOffset(string name)

        => DependencyProperty.Register(name, typeof(double), typeof(GridDecorator),

            new FrameworkPropertyMetadata(0d, FrameworkPropertyMetadataOptions.AffectsRender));



    private static Pen CreatePen(string color, double thickness)

    {

        var pen = new Pen(new SolidColorBrush((Color)ColorConverter.ConvertFromString(color)), thickness);

        pen.Freeze();

        return pen;

    }



    protected override Size MeasureOverride(Size constraint)

    {

        var child = constraint;

        Child?.Measure(child);

        return Child?.DesiredSize ?? new Size(0, 0);

    }



    protected override Size ArrangeOverride(Size arrangeSize)

    {

        Child?.Arrange(new Rect(arrangeSize));

        return arrangeSize;

    }



    protected override void OnRender(DrawingContext dc)

    {

        base.OnRender(dc);

        var bounds = new Rect(RenderSize);

        if (bounds.Width <= 0 || bounds.Height <= 0) return;



        dc.DrawRectangle(new SolidColorBrush(Color.FromRgb(20, 25, 34)), null, bounds);

        var spacing = Math.Max(8, GridSpacing);

        var majorStep = spacing * Math.Max(1, MajorLineEvery);

        var worldLeft = ScrollOffsetX - ContentOffsetX;

        var worldTop = ScrollOffsetY - ContentOffsetY;



        for (var value = Math.Floor(worldLeft / spacing) * spacing; value <= worldLeft + bounds.Width + spacing; value += spacing)

        {

            var x = (value - worldLeft);

            var nearMajor = Math.Abs(value % majorStep) < 0.001 || Math.Abs(value % majorStep - majorStep) < 0.001;

            dc.DrawLine(nearMajor ? MajorPen : MinorPen, new Point(x, 0), new Point(x, bounds.Height));

        }



        for (var value = Math.Floor(worldTop / spacing) * spacing; value <= worldTop + bounds.Height + spacing; value += spacing)

        {

            var y = (value - worldTop);

            var nearMajor = Math.Abs(value % majorStep) < 0.001 || Math.Abs(value % majorStep - majorStep) < 0.001;

            dc.DrawLine(nearMajor ? MajorPen : MinorPen, new Point(0, y), new Point(bounds.Width, y));

        }

    }

}

```
