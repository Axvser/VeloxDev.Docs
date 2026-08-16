# 平台适配器 — `WorkflowView.xaml / WorkflowView.xaml.cs`

Source file from the complete scaffold.

```xml

<!-- ====================== WorkflowView.xaml ====================== -->

<UserControl x:Class="Demo.Views.Workflow.WorkflowView"

             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"

             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"

             xmlns:local="clr-namespace:Demo.Views.Workflow"

             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"

             behaviors:WorkflowSurfaceBehavior.IsEnabled="True"

             behaviors:WorkflowSurfaceBehavior.ScrollViewerName="PART_ScrollViewer"

             behaviors:WorkflowSurfaceBehavior.CanvasName="PART_Canvas"

             behaviors:WorkflowSurfaceBehavior.GridDecoratorName="PART_GridDecorator"

             behaviors:WorkflowSurfaceBehavior.PointerPressSourceName="PART_SurfaceBorder"

             behaviors:WorkflowSurfaceBehavior.MinimapOverlayName="PART_MinimapOverlay">

    <UserControl.Resources>

        <DataTemplate x:Key="NodeTemplate">

            <local:NodeView Width="{Binding Size.Width}"

                            Height="{Binding Size.Height}"

                            Canvas.Left="{Binding Anchor.Horizontal}"

                            Canvas.Top="{Binding Anchor.Vertical}"

                            Panel.ZIndex="{Binding Anchor.Layer}"

                            RenderTransform="{Binding RelativeSource={RelativeSource AncestorType={x:Type local:WorkflowView}}, Path=(behaviors:WorkflowCanvasTransformBehavior.Transform)}" />

        </DataTemplate>

        <DataTemplate x:Key="LinkTemplate">

            <local:LinkView StartLeft="{Binding Sender.Anchor.Horizontal}"

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

        <local:TemplateSelector x:Key="WorkflowTemplateSelector"

                                NodeTemplate="{StaticResource NodeTemplate}"

                                LinkTemplate="{StaticResource LinkTemplate}" />

    </UserControl.Resources>

    <Grid>

        <Border x:Name="PART_SurfaceBorder" Background="#0B1120" BorderBrush="White" BorderThickness="1">

            <local:GridDecorator x:Name="PART_GridDecorator">

                <ScrollViewer x:Name="PART_ScrollViewer"

                              HorizontalScrollBarVisibility="Auto"

                              VerticalScrollBarVisibility="Auto"

                              PanningMode="Both">

                    <Canvas x:Name="PART_Canvas"

                            Width="{Binding Layout.ActualSize.Width}"

                            Height="{Binding Layout.ActualSize.Height}"

                            Background="Transparent"

                            behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"

                            behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />

                </ScrollViewer>

            </local:GridDecorator>

        </Border>

        <local:MinimapOverlay x:Name="PART_MinimapOverlay"

                              HorizontalAlignment="Right"

                              VerticalAlignment="Top"

                              Margin="0,12,12,0"

                              ScrollViewerName="PART_ScrollViewer" />

    </Grid>

</UserControl>

```

```csharp

// ====================== WorkflowView.xaml.cs ======================

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
