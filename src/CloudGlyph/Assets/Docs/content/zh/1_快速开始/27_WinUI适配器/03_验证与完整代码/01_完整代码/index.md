# 完整代码

应用由八个文件加 Windows 清单组成。连线控件在下一页。

## QuickStart.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows10.0.19041.0</TargetFramework>
    <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
    <RootNamespace>MyApp</RootNamespace>
    <ApplicationManifest>app.manifest</ApplicationManifest>
    <Platforms>x86;x64;ARM64</Platforms>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <UseWinUI>true</UseWinUI>
    <WindowsPackageType>None</WindowsPackageType>
    <EnableMsixTooling>true</EnableMsixTooling>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.Windows.SDK.BuildTools" Version="10.0.26100.6584" />
    <PackageReference Include="Microsoft.WindowsAppSDK" Version="1.6.241114003" />
    <PackageReference Include="VeloxDev.WinUI" Version="12.3.0" />
  </ItemGroup>
</Project>
```

## app.manifest

```xml
<?xml version="1.0" encoding="utf-8"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <assemblyIdentity version="1.0.0.0" name="MyApp.app" />
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}" />
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>
```

## App.xaml

```xml
<Application x:Class="MyApp.App"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="using:MyApp">
    <Application.Resources>
        <ResourceDictionary>
            <ResourceDictionary.MergedDictionaries>
                <XamlControlsResources xmlns="using:Microsoft.UI.Xaml.Controls" />
            </ResourceDictionary.MergedDictionaries>
        </ResourceDictionary>
    </Application.Resources>
</Application>
```

## App.xaml.cs

```csharp
using Microsoft.UI.Xaml;

namespace MyApp;

public partial class App : Application
{
    private Window? _window;

    public App() => InitializeComponent();

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _window = new MainWindow();
        _window.Activate();
    }
}
```

## MainWindow.xaml

```xml
<Window x:Class="MyApp.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:local="using:MyApp">
    <local:WorkflowSurface />
</Window>
```

`MainWindow.xaml.cs` 的构造函数里只有 `InitializeComponent()`。

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
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using VeloxDev.WorkflowSystem;

namespace MyApp;

public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }
    public DataTemplate? LinkTemplate { get; set; }

    protected override DataTemplate SelectTemplateCore(object item, DependencyObject container)
        => item switch
        {
            ILinkComponent => LinkTemplate ?? throw new InvalidOperationException("LinkTemplate is not set."),
            INodeComponent => NodeTemplate ?? throw new InvalidOperationException("NodeTemplate is not set."),
            _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
        };
}
```

## WorkflowSurface.xaml

```xml
<UserControl x:Class="MyApp.WorkflowSurface"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="using:MyApp"
             xmlns:behaviors="using:VeloxDev.WorkflowSystem.AttachedBehaviors"
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
                  Canvas.ZIndex="{Binding Anchor.Layer}" Clip="{x:Null}"
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
                            CanRender="{Binding IsVisible}" Canvas.ZIndex="-1" />
        </DataTemplate>
        <local:WorkflowTemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}"
                                        LinkTemplate="{StaticResource LinkTemplate}" />
        <MenuFlyout x:Key="LinkContextMenu">
            <MenuFlyoutItem Text="Delete" Command="{Binding DeleteCommand}" />
        </MenuFlyout>
    </UserControl.Resources>
    <Grid>
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E" BorderBrush="#33FFFFFF" BorderThickness="1">
            <ScrollViewer x:Name="PART_ScrollViewer" HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto" ZoomMode="Disabled">
                <Canvas x:Name="PART_Canvas" Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}" Background="Transparent"
                        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
            </ScrollViewer>
        </Border>
        <behaviors:WorkflowMinimapOverlay x:Name="PART_MinimapOverlay" HorizontalAlignment="Stretch"
                                          VerticalAlignment="Stretch" ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

## WorkflowSurface.xaml.cs

```csharp
using Microsoft.UI.Xaml.Controls;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

namespace MyApp;

public sealed partial class WorkflowSurface : UserControl
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

        Loaded += (_, _) => WorkflowSurfaceBehavior.Refresh(this);
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
