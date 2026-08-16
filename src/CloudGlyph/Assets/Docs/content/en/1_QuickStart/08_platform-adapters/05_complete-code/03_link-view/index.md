# Platform Adapters — `LinkView.xaml / LinkView.xaml.cs`

Source file from the complete scaffold.

```xml

<!-- ====================== LinkView.xaml ====================== -->

<UserControl x:Class="Demo.Views.Workflow.LinkView"

             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"

             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

</UserControl>

```

```csharp

// ====================== LinkView.xaml.cs ======================

using System.Windows;

using System.Windows.Controls;

using System.Windows.Media;



namespace Demo.Views.Workflow;



public partial class LinkView : UserControl

{

    public static readonly DependencyProperty StartLeftProperty = RegisterPointProperty(nameof(StartLeft));

    public static readonly DependencyProperty StartTopProperty = RegisterPointProperty(nameof(StartTop));

    public static readonly DependencyProperty EndLeftProperty = RegisterPointProperty(nameof(EndLeft));

    public static readonly DependencyProperty EndTopProperty = RegisterPointProperty(nameof(EndTop));

    public static readonly DependencyProperty CanRenderProperty =

        DependencyProperty.Register(nameof(CanRender), typeof(bool), typeof(LinkView),

            new PropertyMetadata(true, OnRenderChanged));

    public static readonly DependencyProperty LineColorProperty =

        DependencyProperty.Register(nameof(LineColor), typeof(Color), typeof(LinkView),

            new PropertyMetadata(Colors.White, OnRenderChanged));



    public double StartLeft { get => (double)GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }

    public double StartTop { get => (double)GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }

    public double EndLeft { get => (double)GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }

    public double EndTop { get => (double)GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }

    public bool CanRender { get => (bool)GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }

    public Color LineColor { get => (Color)GetValue(LineColorProperty); set => SetValue(LineColorProperty, value); }



    public LinkView()

    {

        InitializeComponent();

        IsHitTestVisible = false;

        Panel.SetZIndex(this, -100);

    }



    private static DependencyProperty RegisterPointProperty(string name)

        => DependencyProperty.Register(name, typeof(double), typeof(LinkView), new PropertyMetadata(0d, OnRenderChanged));



    private static void OnRenderChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)

        => ((LinkView)d).InvalidateVisual();



    protected override void OnRender(DrawingContext ctx)

    {

        base.OnRender(ctx);

        if (!CanRender) return;

        ctx.DrawLine(new Pen(new SolidColorBrush(LineColor), 1.5),

            new Point(StartLeft, StartTop), new Point(EndLeft, EndTop));

    }

}

```
