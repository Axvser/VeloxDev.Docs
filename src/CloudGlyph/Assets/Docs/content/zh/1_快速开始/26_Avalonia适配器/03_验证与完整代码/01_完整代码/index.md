# 完整代码

## QuickStart.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <AvaloniaUseCompiledBindingsByDefault>true</AvaloniaUseCompiledBindingsByDefault>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Avalonia" Version="11.1.0" />
    <PackageReference Include="Avalonia.Desktop" Version="11.1.0" />
    <PackageReference Include="Avalonia.Themes.Fluent" Version="11.1.0" />
    <PackageReference Include="VeloxDev.Avalonia" Version="12.3.0" />
  </ItemGroup>
</Project>
```

## Program.cs

```csharp
using System;
using Avalonia;

namespace MyApp;

internal static class Program
{
    [STAThread]
    public static void Main(string[] args) => BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);

    public static AppBuilder BuildAvaloniaApp() =>
        AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace();
}
```

## App.axaml

```xml
<Application xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             x:Class="MyApp.App" RequestedThemeVariant="Dark">
    <Application.Styles><FluentTheme /></Application.Styles>
</Application>
```

## App.axaml.cs

```csharp
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;

namespace MyApp;

public partial class App : Application
{
    public override void Initialize() => AvaloniaXamlLoader.Load(this);

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            desktop.MainWindow = new Window { Title = "Workflow", Width = 1100, Height = 720, Content = new WorkflowSurface() };
        }

        base.OnFrameworkInitializationCompleted();
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

[WorkflowBuilder.Tree<VirtualizeHelper>] public partial class TreeViewModel { public TreeViewModel() => InitializeWorkflow(); }

[WorkflowBuilder.Node<NodeHelper>]
public partial class NodeViewModel
{
    public NodeViewModel() => InitializeWorkflow();

    [VeloxProperty] private string _name = string.Empty;

    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>] public partial class SlotViewModel { public SlotViewModel() => InitializeWorkflow(); }

[WorkflowBuilder.Link<LinkHelper>] public partial class LinkViewModel { public LinkViewModel() => InitializeWorkflow(); }
```

## WorkflowTemplateSelector.cs

```csharp
using System;
using Avalonia.Controls;
using Avalonia.Controls.Templates;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : IDataTemplate
{
    public IDataTemplate? NodeTemplate { get; set; }
    public IDataTemplate? LinkTemplate { get; set; }

    public Control Build(object? parameter)
        => Select(parameter).Build(parameter)
           ?? throw new InvalidOperationException($"The selected template could not build {parameter?.GetType().FullName}.");

    public bool Match(object? data) => data is INodeComponent or ILinkComponent;

    private IDataTemplate Select(object? item) => item switch
    {
        ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
        INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
        _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
    };
}
```

## LinkView.cs

```csharp
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Immutable;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class LinkView : Control
{
    private const double PullMinimum = 40;

    public static readonly StyledProperty<double> StartLeftProperty = AvaloniaProperty.Register<LinkView, double>(nameof(StartLeft));
    public static readonly StyledProperty<double> StartTopProperty = AvaloniaProperty.Register<LinkView, double>(nameof(StartTop));
    public static readonly StyledProperty<double> EndLeftProperty = AvaloniaProperty.Register<LinkView, double>(nameof(EndLeft));
    public static readonly StyledProperty<double> EndTopProperty = AvaloniaProperty.Register<LinkView, double>(nameof(EndTop));
    public static readonly StyledProperty<bool> CanRenderProperty = AvaloniaProperty.Register<LinkView, bool>(nameof(CanRender), true);

    public double StartLeft { get => GetValue(StartLeftProperty); set => SetValue(StartLeftProperty, value); }
    public double StartTop { get => GetValue(StartTopProperty); set => SetValue(StartTopProperty, value); }
    public double EndLeft { get => GetValue(EndLeftProperty); set => SetValue(EndLeftProperty, value); }
    public double EndTop { get => GetValue(EndTopProperty); set => SetValue(EndTopProperty, value); }
    public bool CanRender { get => GetValue(CanRenderProperty); set => SetValue(CanRenderProperty, value); }

    static LinkView() => AffectsRender<LinkView>(
        StartLeftProperty, StartTopProperty, EndLeftProperty, EndTopProperty, CanRenderProperty);

    protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
    {
        base.OnPropertyChanged(change);
        if (change.Property == DataContextProperty)
        {
            if (change.OldValue is ILinkComponent old && !ReferenceEquals(old, change.NewValue))
                old.PublishCurve(null);
            InvalidateVisual();
        }
    }

    public override void Render(DrawingContext context)
    {
        if (!CanRender) return;
        if (DataContext is ILinkComponent link && !link.IsRenderReady()) return;

        var curve = LinkCurve.BuildLinkCubic(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        if (DataContext is ILinkComponent bound) bound.PublishCurve(curve, this);

        var p = LinkCurve.LinkCurvePoints(DataContext as ILinkComponent,
            StartLeft, StartTop, EndLeft, EndTop, PullMinimum);
        var geometry = new StreamGeometry();
        using (var ctx = geometry.Open())
        {
            ctx.BeginFigure(new Point(p[0].X, p[0].Y), false);
            ctx.CubicBezierTo(new Point(p[1].X, p[1].Y), new Point(p[2].X, p[2].Y), new Point(p[3].X, p[3].Y));
        }

        context.DrawGeometry(null, new Pen(new ImmutableSolidColorBrush(Colors.WhiteSmoke), 2), geometry);
    }
}
```

## WorkflowSurface.axaml

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="https://github.com/avaloniaui"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="using:MyApp" xmlns:vm="using:MyApp"
             xmlns:framework="using:VeloxDev.WorkflowSystem"
             xmlns:behaviors="using:VeloxDev.WorkflowSystem.AttachedBehaviors"
             x:DataType="vm:TreeViewModel"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True" behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay"
             behaviors:WorkflowSurfaceBehavior.LinkMenuKey="LinkContextMenu">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate" DataType="vm:NodeViewModel">
            <Grid Width="{Binding Size.Width}" Height="{Binding Size.Height}"
                  Canvas.Left="{Binding Anchor.Horizontal}" Canvas.Top="{Binding Anchor.Vertical}"
                  ZIndex="{Binding Anchor.Layer}"
                  RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}"
                  behaviors:WorkflowSlotLayoutBehavior.IsEnabled="True" behaviors:WorkflowSlotLayoutBehavior.SlotNames="PART_InputSlot"
                  behaviors:WorkflowSlotLayoutBehavior.SlotEnumeratorNames="PART_OutputSlots" behaviors:WorkflowSlotLayoutBehavior.CoordinateHostName="PART_Canvas">
                <Border Background="#FFFFFFFF" BorderBrush="#331E1E1E" BorderThickness="1" CornerRadius="6" />
                <Grid Height="32" VerticalAlignment="Top" Background="Transparent"
                      behaviors:WorkflowNodeDragBehavior.IsEnabled="True"
                      behaviors:WorkflowNodeDragBehavior.CoordinateHostName="PART_Canvas">
                    <TextBlock Text="{Binding Name}" Margin="10,8" />
                </Grid>
                <Ellipse x:Name="PART_InputSlot" DataContext="{Binding InputSlot}" Width="14" Height="14"
                         Fill="#FF1E1E1E" Stroke="White" HorizontalAlignment="Left" VerticalAlignment="Center"
                         behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                <ItemsControl x:Name="PART_OutputSlots" ItemsSource="{Binding OutputSlots.Items}" Margin="10" VerticalAlignment="Bottom">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate>
                            <Grid Margin="0,2">
                                <TextBlock Text="{Binding Name}" />
                                <Ellipse DataContext="{Binding Slot}" Width="12" Height="12" Fill="#FF1E1E1E" Stroke="White"
                                         HorizontalAlignment="Right" behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True" />
                            </Grid>
                        </DataTemplate>
                    </ItemsControl.ItemTemplate>
                </ItemsControl>
            </Grid>
        </DataTemplate>
        <DataTemplate x:Key="LinkTemplate" DataType="framework:ILinkComponent">
            <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}" StartTop="{Binding Sender.Anchor.Vertical}"
                            EndLeft="{Binding Receiver.Anchor.Horizontal}" EndTop="{Binding Receiver.Anchor.Vertical}"
                            CanRender="{Binding IsVisible}" Width="{Binding $parent[Canvas].Bounds.Width}" Height="{Binding $parent[Canvas].Bounds.Height}" ZIndex="-1" IsHitTestVisible="False"
                            RenderTransform="{Binding $parent[local:WorkflowSurface].(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}" LinkTemplate="{StaticResource LinkTemplate}" />
        <ContextMenu x:Key="LinkContextMenu">
            <MenuItem Header="Delete" Command="{ReflectionBinding DeleteCommand}" />
        </ContextMenu>
    </UserControl.Resources>
    <Grid>
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
            <ScrollViewer x:Name="PART_ScrollViewer" HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto" IsScrollInertiaEnabled="False">
                <Canvas x:Name="PART_Canvas" Width="{Binding Layout.ActualSize.Width}" Height="{Binding Layout.ActualSize.Height}"
                        Background="Transparent" behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
            </ScrollViewer>
        </Border>
        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay" HorizontalAlignment="Stretch"
                                          VerticalAlignment="Stretch" ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

## WorkflowSurface.axaml.cs

```csharp
using Avalonia.Controls;
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

## 运行声明

- ⚠️ 未实际运行 —— 仅做了静态核对。附着属性、`IDataTemplate` 选择器契约、`Control.Render` 入口、`AffectsRender` 与 ViewModel 特性均对照过 `Src/Adapters/VeloxDev.Avalonia/`、`Src/Core/VeloxDev.Core/` 与 `Examples/Workflow/Avalonia Trimmed/`。完整文件集在本次写作中未编译、未执行。
