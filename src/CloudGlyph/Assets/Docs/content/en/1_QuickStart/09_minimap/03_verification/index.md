# Verification

The overlay is easiest to verify on a tree that is larger than the viewport. The runnable reference is the Avalonia Trimmed demo; the WPF full workbench has the same overlay. The host below is the [View hosting and virtualization](../../08_view-hosting-virtualization/03_verification/index.md) sample with the minimap added.

## Run the reference

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

## Check each behaviour

1. **Placement.** The minimap sits in the top-right of the canvas, with a 12 px gap.
2. **Thumbnails.** Every node appears as a small block at its relative position; moving a node moves its block.
3. **Viewport block.** The rectangle matches what the surface currently shows. Scrolling moves it.
4. **Drag.** Press inside the minimap and drag: the canvas scrolls so the pressed point stays under the pointer.
5. **Toggle.** Untick the minimap check-box: the map disappears on the next render; the canvas keeps working.
6. **Resize.** Shrink the window: the map clamps to the free corner and never overlaps the scrollbars.

The WPF headless suite renders the overlay and asserts that it produces node and viewport geometry and that a drag moves the surface `ScrollViewer` (`Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/MinimapHeadlessTests.cs`).

## Complete code

### `TreeView.xaml`

The view models and the template selector are the ones on [View hosting and virtualization](../../08_view-hosting-virtualization/03_verification/index.md). Only the surface name and the overlay element change.

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
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">
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

    <Grid>
        <Border x:Name="PART_SurfaceBorder" Background="#1E1E1E">
            <ScrollViewer x:Name="PART_ScrollViewer"
                          HorizontalScrollBarVisibility="Auto"
                          VerticalScrollBarVisibility="Auto">
                <Canvas x:Name="PART_Canvas"
                        Width="{Binding Layout.ActualSize.Width}"
                        Height="{Binding Layout.ActualSize.Height}"
                        Background="Transparent"
                        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
            </ScrollViewer>
        </Border>

        <local:BrandMinimap x:Name="PART_MinimapOverlay"
                            HorizontalAlignment="Stretch"
                            VerticalAlignment="Stretch"
                            ScrollViewerName="PART_ScrollViewer"
                            IsMinimapVisible="True" />

        <CheckBox Content="Minimap" HorizontalAlignment="Right" VerticalAlignment="Bottom" Margin="12"
                  IsChecked="{Binding IsMinimapVisible, ElementName=PART_MinimapOverlay}" />
    </Grid>
</UserControl>
```

### `BrandMinimap.cs`

```csharp
using System.Windows.Media;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;

namespace Demo;

public sealed class BrandMinimap : WorkflowMinimapOverlay
{
    public BrandMinimap()
    {
        MinimapBackground = new SolidColorBrush(Color.FromArgb(0xD2, 0x1F, 0x1F, 0x1F));
        MinimapBorderBrush = new SolidColorBrush(Color.FromArgb(0xDC, 0x40, 0x40, 0x40));
        NodeBrush = new SolidColorBrush(Color.FromArgb(0xDC, 0x6E, 0x8B, 0xFF));
        ViewportStroke = new SolidColorBrush(Color.FromArgb(0xF0, 0xE7, 0xE7, 0xE7));
    }

    protected override void DrawMinimap(DrawingContext dc, MinimapDrawContext context)
    {
        base.DrawMinimap(dc, context);
    }
}
```

The override is optional; it is shown so a custom pass has a place to start. Calling `base` keeps the default frame, thumbnails and viewport block.

## Run declaration

⚠️ Not actually run — statically verified only. Property names and defaults are taken from `Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs`; the drag path is `MinimapPipelineCore.PointerPressed/Moved/Released`, asserted by `MinimapHeadlessTests`. No window was launched while writing this page.
