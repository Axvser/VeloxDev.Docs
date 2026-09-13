# 平台适配器 - `WorkflowView.xaml / WorkflowView.xaml.cs`

`dotnet new wpf-v-tree -n WorkflowView -ns Demo.Views.Workflow` 的精确输出（模板默认颜色已替换）。表面宿主应用 `WorkflowSurfaceBehavior` 并启用缩放，同时命名了它在加载时解析的部件：`PART_ScrollViewer`、`PART_Canvas`、`PART_GridDecorator`、`PART_SurfaceBorder`，以及通过 `PART_MinimapOverlay` 命名的小地图。把 `DataContext` 绑定到 `IWorkflowTreeViewModel`；画布通过绑定 `Helper.VisibleItems` 的 `ViewPool` 实现虚拟化。

```xml
<!-- VeloxDev customization: Generate the Node, Slot, Link, selector, minimap, and grid-decorator templates, then update the local type names below if you renamed them. -->
<UserControl x:Class="Demo.Views.Workflow.WorkflowView"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:local="clr-namespace:Demo.Views.Workflow"
             xmlns:workflowViews="clr-namespace:Demo.Views.Workflow"
             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"
             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ZoomEnabled="True"
             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"
             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"
             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"
             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"
             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">
    <UserControl.Resources>
        <DataTemplate x:Key="NodeTemplate">
            <workflowViews:NodeView Width="{Binding Size.Width}"
                                    Height="{Binding Size.Height}"
                                    Canvas.Left="{Binding Anchor.Horizontal}"
                                    Canvas.Top="{Binding Anchor.Vertical}"
                                    Panel.ZIndex="{Binding Anchor.Layer}"
                                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowView}}, Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <DataTemplate x:Key="LinkTemplate">
            <workflowViews:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"
                                    StartTop="{Binding Sender.Anchor.Vertical}"
                                    EndLeft="{Binding Receiver.Anchor.Horizontal}"
                                    EndTop="{Binding Receiver.Anchor.Vertical}"
                                    CanRender="{Binding IsVisible}"
                                    LineColor="#DDFFFFFF"
                                    Width="{Binding ElementName=PART_Canvas, Path=ActualWidth}"
                                    Height="{Binding ElementName=PART_Canvas, Path=ActualHeight}"
                                    Panel.ZIndex="-1"
                                    RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowView}}, Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />
        </DataTemplate>
        <workflowViews:TemplateSelector x:Key="WorkflowTemplateSelector"
                                        NodeTemplate="{StaticResource NodeTemplate}"
                                        LinkTemplate="{StaticResource LinkTemplate}" />
    </UserControl.Resources>
    <Grid>
        <Border x:Name="PART_SurfaceBorder"
                Background="#1E1E1E"
                BorderBrush="#33FFFFFF"
                BorderThickness="1">
            <workflowViews:GridDecorator x:Name="PART_GridDecorator">
                <ScrollViewer x:Name="PART_ScrollViewer"
                              HorizontalScrollBarVisibility="Auto"
                              VerticalScrollBarVisibility="Auto"
                              PanningMode="Both">
                    <Canvas x:Name="PART_Canvas"
                            Width="{Binding Layout.ActualSize.Width}"
                            Height="{Binding Layout.ActualSize.Height}"
                            Background="Transparent"
                            behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
                            behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}">
                        <Canvas.RenderTransform>
                            <TranslateTransform X="{Binding RulerThickness, ElementName=PART_GridDecorator}"
                                                Y="{Binding RulerThickness, ElementName=PART_GridDecorator}" />
                        </Canvas.RenderTransform>
                    </Canvas>
                </ScrollViewer>
            </workflowViews:GridDecorator>
        </Border>
        <workflowViews:MinimapOverlay x:Name="PART_MinimapOverlay"
                                      HorizontalAlignment="Right"
                                      VerticalAlignment="Top"
                                      Margin="0,12,12,0"
                                      ScrollViewerName="PART_ScrollViewer" />
    </Grid>
</UserControl>
```

```csharp
// VeloxDev customization: Initialize tree-specific UI behavior here; provide an IWorkflowTreeViewModel as the data context.
using System.Windows.Controls;

namespace Demo.Views.Workflow;

public partial class WorkflowView : UserControl
{
    public WorkflowView()
    {
        InitializeComponent();
    }
}
```
