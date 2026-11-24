# Complete Code

Eight files make the runnable application. `TargetFramework` is `net8.0-windows`; `UseWPF` is required.

## QuickStart.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="VeloxDev.WPF" Version="12.3.0" />
  </ItemGroup>
</Project>
```

## App.xaml

```xml
<Application x:Class="MyApp.App"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             StartupUri="MainWindow.xaml" />
```

`App.xaml.cs` declares the empty `public partial class App : Application` that pairs with this markup.

## MainWindow.xaml

```xml
<Window x:Class="MyApp.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:local="clr-namespace:MyApp"
        Title="Workflow" Width="1100" Height="720" Background="#1E1E1E">
    <local:WorkflowSurface />
</Window>
```

`MainWindow.xaml.cs` contains only `InitializeComponent()` in the constructor.

## ViewModels.cs

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public enum Kind { A, B, C }

internal sealed class VirtualizeHelper() : TreeHelper(200) { }

[WorkflowBuilder.Tree<VirtualizeHelper>]
public partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper>]
public partial class NodeViewModel
{
    public NodeViewModel() => InitializeWorkflow();

    [VeloxProperty] private string _name = string.Empty;

    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();
}
```

## WorkflowTemplateSelector.cs

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }
    public DataTemplate? LinkTemplate { get; set; }

    public override DataTemplate SelectTemplate(object item, DependencyObject container)
        => item switch
        {
            ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
            INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
            _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
        };
}
```

## LinkView.cs

```csharp
using System.Windows;
using System.Windows.Media;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class LinkView : FrameworkElement
{
    private const double PullMinimum = 40;

    public static readonly DependencyProperty StartLeftProperty = DependencyProperty.Register(
        nameof(StartLeft), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty StartTopProperty = DependencyProperty.Register(
        nameof(StartTop), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty EndLeftProperty = DependencyProperty.Register(
        nameof(EndLeft), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty EndTopProperty = DependencyProperty.Register(
        nameof(EndTop), typeof(double), typeof(LinkView), new FrameworkPropertyMetadata(0d, OnGeometryChanged));
    public static readonly DependencyProperty CanRenderProperty = DependencyProperty.Register(
        nameof(CanRender), typeof(bool), typeof(LinkView), new FrameworkPropertyMetadata(true, OnGeometryChanged));

    public double StartLeft { get => (double)GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }
    public double StartTop { get => (double)GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }
    public double EndLeft { get => (double)GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }
    public double EndTop { get => (double)GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }
    public bool CanRender { get => (bool)GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }

    public LinkView()
    {
        DataContextChanged += (_, e) =>
        {
            if (e.OldValue is ILinkComponent old) old.PublishCurve(null);
            InvalidateVisual();
        };
    }

    private static void OnGeometryChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        => ((LinkView)d).InvalidateVisual();

    protected override void OnRender(DrawingContext dc)
    {
        if (!CanRender) return;
        if (DataContext is ILinkComponent link && !link.IsRenderReady()) return;

        var curve = LinkCurve.BuildLinkCubic(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        if (DataContext is ILinkComponent bound) bound.PublishCurve(curve, this);

        var p = LinkCurve.LinkCurvePoints(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        var geometry = new StreamGeometry();
        using (var context = geometry.Open())
        {
            context.BeginFigure(new Point(p[0].X, p[0].Y), false, false);
            context.BezierTo(new Point(p[1].X, p[1].Y), new Point(p[2].X, p[2].Y),
                new Point(p[3].X, p[3].Y), true, false);
        }

        dc.DrawGeometry(null, new Pen(Brushes.WhiteSmoke, 2), geometry);
    }
}
```

## WorkflowSurface.xaml

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:MyApp"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <Grid Width="{Binding Size.Width}" Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}" Canvas.Top="{Binding Anchor.Vertical}"
                  Panel.ZIndex="{Binding Anchor.Layer}"
                  RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                                            Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
                  behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                  behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                  behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                  behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Border Background="#FFFFFFFF" BorderBrush="#331E1E1E" BorderThickness="1" CornerRadius="6" />
                <Grid Height="32" VerticalAlignment="Top" Background="Transparent"
                      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                    <TextBlock Text="{Binding Name}" Margin="10,8" />
                </Grid>
                <Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}"
                         Width="14" Height="14" Fill="#FF1E1E1E" Stroke="White"
                         HorizontalAlignment="Left" VerticalAlignment="Center"
                         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                <ItemsControl x:Name="PART_OutputSlots" ItemsSource="{Binding OutputSlots.Items}"
                              Margin="10" VerticalAlignment="Bottom">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate>
                            <Grid Margin="0,2">
                                <TextBlock Text="{Binding Name}" />
                                <Ellipse DataContext="{Binding Slot}" Width="12" Height="12"
                                         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Right"
                                         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                            </Grid>
                        </DataTemplate>
                    </ItemsControl.ItemTemplate>
                </ItemsControl>
            </Grid>
        </DataTemplate>
        <DataTemplate x:Key="LinkTemplate">
            <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                            StartTop="{Binding Sender.Anchor.Vertical}"
                            EndLeft="{Binding Receiver.Anchor.Horizontal}"
                            EndTop="{Binding Receiver.Anchor.Vertical}"
                            CanRender="{Binding IsVisible}"
                            Width="{Binding ElementName=PART_Canvas, Path=ActualWidth}"
                            Height="{Binding ElementName=PART_Canvas, Path=ActualHeight}"
                            Panel.ZIndex="-1" IsHitTestVisible="False"
                            RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowSurface}},
                                                      Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}"
                                        LinkTemplate="{StaticResource LinkTemplate}" />
        <ContextMenu x:Key="LinkContextMenu">
            <MenuItem Header="Delete" Command="{Binding DeleteCommand}" />
        </ContextMenu>
    </UserControl.Resources>
    <Grid>
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
            <ScrollViewer x:Name="PART_ScrollViewer" HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas" Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}" Background="Transparent"
                        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
            </ScrollViewer>
        </Border>
        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay"
                                          HorizontalAlignment="Stretch" VerticalAlignment="Stretch"
                                          ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

## WorkflowSurface.xaml.cs

```csharp
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public partial class WorkflowSurface : UserControl
{
    private ITreeComponent? _tree;
    private IInputEvents? _events;

    public WorkflowSurface()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        var nodes = LoadTree(tree);
        Connect(tree, nodes[0], nodes[1]);
        DataContext = tree;
        BindTree(tree);
    }

    private static NodeViewModel[] LoadTree(TreeViewModel tree)
    {
        tree.Layout.NegativeOffset = new Offset(320, 260);
        var nodes = new NodeViewModel[3];

        for (var i = 0; i < nodes.Length; i++)
        {
            nodes[i] = new NodeViewModel
            {
                Name = $"Node {i + 1}",
                Size = new Size(220, 120),
                Anchor = new Anchor(120 + (i * 280), 140, 0)
            };
            tree.CreateNodeCommand.Execute(nodes[i]);
        }

        return nodes;
    }

    private static void Connect(TreeViewModel tree, NodeViewModel sender, NodeViewModel receiver)
    {
        sender.OutputSlots.SetSelector(typeof(Kind));
        if (sender.OutputSlots.Items.Count == 0) return;

        tree.GetHelper().SendConnection(sender.OutputSlots.Items[0].Slot);
        tree.GetHelper().ReceiveConnection(receiver.InputSlot);
    }

    private void BindTree(ITreeComponent tree)
    {
        if (tree.GetHelper() is not IInputEvents events) return;
        _tree = tree;
        _events = events;
        events.Input.KeyDown += OnKeyDown;
        events.Input.PointerWheelChanged += OnWheel;
    }

    private void OnWheel(object? sender, PointerWheelEventArgs e)
    {
        if (_tree is not { } tree || !e.Modifiers.HasFlag(InputModifiers.Shift)) return;

        e.Handle.PreventDefault = true;
        WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
    }

    private void OnKeyDown(object? sender, KeyDownEventArgs e)
    {
        if (_tree is not { } tree) return;

        if (e.Key == InputKey.Delete && e.Target is ILinkComponent link && link.DeleteCommand.CanExecute(null))
        {
            link.DeleteCommand.Execute(null);
            return;
        }

        if (!e.Modifiers.HasFlag(InputModifiers.Control)) return;

        var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
        if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
        else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
        else return;

        e.Handle.PreventDefault = true;
    }
}
```

## Run Declaration

- ⚠️ Not actually run — statically verified only. The attached property names, generated attributes, helper and connection APIs, and file paths were checked against `Src/Adapters/VeloxDev.WPF/`, `Src/Core/VeloxDev.Core/` and `Examples/Workflow/WPF Trimmed/Demo/`. The complete file set was not compiled or executed in the writing session.
