# 完整代码

共享应用由十一个文件组成；Windows 入口在下一页。工程只目标 Windows TFM，因此不需要 Android、iOS 或 Mac Catalyst 工作负载也能构建；要跑其他平台时再加相应 TFM 与平台目录。

## QuickStart.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0-windows10.0.19041.0</TargetFramework>
    <OutputType>Exe</OutputType>
    <RootNamespace>MyApp</RootNamespace>
    <UseMaui>true</UseMaui>
    <SingleProject>true</SingleProject>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <MauiVersion>10.0.20</MauiVersion>
    <WindowsPackageType>None</WindowsPackageType>
    <SupportedOSPlatformVersion>10.0.17763.0</SupportedOSPlatformVersion>
    <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.Maui.Controls" Version="$(MauiVersion)" />
    <PackageReference Include="Microsoft.WindowsAppSDK" Version="1.7.250909003" />
    <PackageReference Include="VeloxDev.MAUI" Version="12.3.0" />
  </ItemGroup>
</Project>
```

## MauiProgram.cs

```csharp
using Microsoft.Maui.Hosting;

namespace MyApp;

public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder.UseMauiApp<App>();
        return builder.Build();
    }
}
```

## App.xaml

```xml
<Application xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             xmlns:local="clr-namespace:MyApp"
             x:Class="MyApp.App">
</Application>
```

## App.xaml.cs

```csharp
namespace MyApp;

public partial class App : Application
{
    public App() => InitializeComponent();

    protected override Window CreateWindow(IActivationState? activationState)
        => new(new MainPage());
}
```

## MainPage.xaml

```xml
<ContentPage xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             xmlns:local="clr-namespace:MyApp"
             x:Class="MyApp.MainPage"
             Title="Workflow" BackgroundColor="#020617">
    <local:TreeView x:Name="WorkflowTree" Margin="16" />
</ContentPage>
```

## MainPage.xaml.cs

```csharp
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public partial class MainPage : ContentPage
{
    public MainPage()
    {
        InitializeComponent();

        var tree = new TreeViewModel();
        var nodes = LoadTree(tree);
        Connect(tree, nodes[0], nodes[1]);
        WorkflowTree.BindingContext = tree;
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
                Size = new VeloxDev.WorkflowSystem.Size(220, 120),
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
}
```

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
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }

    protected override DataTemplate OnSelectTemplate(object item, BindableObject container)
        => item is INodeComponent
            ? NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set.")
            : throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}");
}
```

## PlainGridDecorator.cs

```csharp
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class PlainGridDecorator : Grid, IWorkflowGridDecorator
{
    public static readonly BindableProperty ScrollOffsetXProperty = BindableProperty.Create(nameof(ScrollOffsetX), typeof(double), typeof(PlainGridDecorator), 0d);
    public static readonly BindableProperty ScrollOffsetYProperty = BindableProperty.Create(nameof(ScrollOffsetY), typeof(double), typeof(PlainGridDecorator), 0d);
    public static readonly BindableProperty ContentOffsetXProperty = BindableProperty.Create(nameof(ContentOffsetX), typeof(double), typeof(PlainGridDecorator), 0d);
    public static readonly BindableProperty ContentOffsetYProperty = BindableProperty.Create(nameof(ContentOffsetY), typeof(double), typeof(PlainGridDecorator), 0d);

    public double ScrollOffsetX { get => (double)GetValue(ScrollOffsetXProperty); set => SetValue(ScrollOffsetXProperty, value); }
    public double ScrollOffsetY { get => (double)GetValue(ScrollOffsetYProperty); set => SetValue(ScrollOffsetYProperty, value); }
    public double ContentOffsetX { get => (double)GetValue(ContentOffsetXProperty); set => SetValue(ContentOffsetXProperty, value); }
    public double ContentOffsetY { get => (double)GetValue(ContentOffsetYProperty); set => SetValue(ContentOffsetYProperty, value); }
    public double RulerBand => 0d;
}
```

## TreeView.xaml

```xml
<ContentView xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             xmlns:local="clr-namespace:MyApp"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.MAUI"
             x:Class="MyApp.TreeView" x:Name="Root"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True" behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu">
    <ContentView.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <Border BackgroundColor="#FFFFFFFF" Stroke="#331E1E1E" StrokeThickness="1" StrokeShape="RoundRectangle 6"
                    WidthRequest="{Binding Size.Width}" HeightRequest="{Binding Size.Height}"
                    behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True"
                    behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                    behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots"
                    behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Grid RowDefinitions="32,*">
                    <Grid Grid.Row="0" BackgroundColor="Transparent"
                          behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                          behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                        <Label Text="{Binding Name}" Margin="10,0" VerticalTextAlignment="Center" />
                    </Grid>
                    <Ellipse x:Name="PART_InputSlot" Grid.Row="1" BindingContext="{Binding InputSlot}" WidthRequest="14" HeightRequest="14"
                             Fill="#FF1E1E1E" Stroke="White" HorizontalOptions="Start" VerticalOptions="Center"
                             behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                    <VerticalStackLayout x:Name="PART_OutputSlots" Grid.Row="1" Margin="10" Spacing="4"
                                         BindableLayout.ItemsSource="{Binding OutputSlots.Items}">
                        <BindableLayout.ItemTemplate>
                            <DataTemplate>
                                <Grid ColumnDefinitions="*,Auto">
                                    <Label Text="{Binding Name}" />
                                    <Ellipse Grid.Column="1" BindingContext="{Binding Slot}" WidthRequest="12" HeightRequest="12"
                                             Fill="#FF1E1E1E" Stroke="White" behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                                </Grid>
                            </DataTemplate>
                        </BindableLayout.ItemTemplate>
                    </VerticalStackLayout>
                </Grid>
            </Border>
        </DataTemplate>
        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector" NodeTemplate="{StaticResource NodeTemplate}" />
        <MenuFlyout x:Key="LinkContextMenu">
            <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
        </MenuFlyout>
    </ContentView.Resources>
    <Grid>
        <Border x:Name="PART_SurfaceBorder" Stroke="#33FFFFFF" StrokeThickness="1" StrokeShape="RoundRectangle 3" BackgroundColor="#1E1E1E">
            <local:PlainGridDecorator x:Name="PART_GridDecorator">
                <behaviors:WorkflowLinkOverlay x:Name="PART_LinkLayer"
                                               WorkflowTree="{Binding BindingContext, Source={x:Reference Root}}"
                                               InteractionSource="{x:Reference Root}"
                                               ScrollOffsetX="{Binding ScrollOffsetX, Source={x:Reference PART_GridDecorator}}"
                                               ScrollOffsetY="{Binding ScrollOffsetY, Source={x:Reference PART_GridDecorator}}"
                                               ContentOffsetX="{Binding ContentOffsetX, Source={x:Reference PART_GridDecorator}}"
                                               ContentOffsetY="{Binding ContentOffsetY, Source={x:Reference PART_GridDecorator}}"
                                               RulerThickness="0" StrokeWidth="2" />
                <ScrollView x:Name="PART_ScrollViewer" Orientation="Both">
                    <AbsoluteLayout x:Name="PART_Canvas" BackgroundColor="Transparent"
                                    behaviors:ViewPool.ItemsSource="{Binding BindingContext.Helper.VisibleItems, Source={x:Reference Root}}"
                                    behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
                </ScrollView>
            </local:PlainGridDecorator>
        </Border>
        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay" HorizontalOptions="Fill"
                                          VerticalOptions="Fill" ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</ContentView>
```

## TreeView.xaml.cs

```csharp
using Microsoft.Maui.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public partial class TreeView : ContentView
{
    private ITreeComponent? _tree;
    private IInputEvents? _events;

    public TreeView()
    {
        InitializeComponent();
        BindingContextChanged += (_, _) => BindTree(BindingContext as ITreeComponent);
    }

    private void BindTree(ITreeComponent? tree)
    {
        if (_events is not null)
        {
            _events.Input.KeyDown -= OnKeyDown;
            _events.Input.PointerWheelChanged -= OnWheel;
        }

        _events = null;
        _tree = tree;
        if (tree?.GetHelper() is not IInputEvents events) return;

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
        if (e.Handle.PreventDefault || _tree is not { } tree) return;

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
