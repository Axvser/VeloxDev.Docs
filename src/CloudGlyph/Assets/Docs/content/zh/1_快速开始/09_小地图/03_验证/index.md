# 验证

在比视口更大的树上最容易验证覆盖层。可运行参考是 Avalonia Trimmed 示例；WPF 完整工作台有同一个覆盖层。下面的宿主是[视图托管与虚拟化](../../08_视图托管与虚拟化/03_验证/index.md)示例加上小地图。

## 运行参考

```powershell
dotnet run --project "Examples/Workflow/Avalonia Trimmed/Demo/Demo.Desktop/Demo.Desktop.csproj"
```

## 逐项检查

1. **放置。** 小地图在画布右上角，间隙 12 px。
2. **缩略块。** 每个节点按相对位置显示为一个小块；移动节点会移动它的块。
3. **视口块。** 矩形与表面当前显示范围一致；滚动时它移动。
4. **拖动。** 在小地图里按下拖动：画布滚动，按下点始终留在指针下。
5. **开关。** 取消勾选：地图在下一次渲染消失，画布照常工作。
6. **缩放窗口。** 缩小窗口时地图夹到可用角落，不会压住滚动条。

WPF 无头套件渲染覆盖层，断言它产出节点与视口几何，并断言拖动会移动表面的 `ScrollViewer`（`Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/MinimapHeadlessTests.cs`）。

## 完整代码

### `TreeView.xaml`

视图模型与模板选择器来自[视图托管与虚拟化](../../08_视图托管与虚拟化/03_验证/index.md)。这里只改表面命名与覆盖层元素。

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

重写是可选的；写出来是为了给自定义绘制一个起点。调用 `base` 保留默认外框、缩略块与视口块。

## 运行声明

⚠️ 未实际运行——仅静态核对。属性名与默认值取自 `Src/Adapters/VeloxDev.WPF/WorkflowSystem/AttachedBehaviors/WorkflowMinimapOverlay.cs`；拖动路径是 `MinimapPipelineCore.PointerPressed/Moved/Released`，由 `MinimapHeadlessTests` 断言。撰写本页时没有启动窗口。
