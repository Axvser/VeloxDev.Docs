# 平台适配器 — `SlotView.xaml / SlotView.xaml.cs`

Source file from the complete scaffold.

```xml

<!-- ====================== SlotView.xaml ====================== -->

<UserControl x:Class="Demo.Views.Workflow.SlotView"

             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"

             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"

             xmlns:behaviors="clr-namespace:VeloxDev.WorkflowSystem.AttachedBehaviors;assembly=VeloxDev.WPF"

             Background="Transparent"

             behaviors:WorkflowSlotConnectionBehavior.IsEnabled="True"

             MouseLeftButtonUp="OnPointerReleased"

             MouseLeftButtonDown="OnPointerPressed">

    <Viewbox>

        <Path Fill="{Binding Foreground, RelativeSource={RelativeSource AncestorType=UserControl}}"

              Data="M 0,0 A 10,10 0 1 0 20,0 A 10,10 0 1 0 0,0 Z" />

    </Viewbox>

</UserControl>

```

```csharp

// ====================== SlotView.xaml.cs ======================

using System.Windows;

using System.Windows.Controls;

using System.Windows.Input;

using System.Windows.Media;

using VeloxDev.WorkflowSystem;



namespace Demo.Views.Workflow;



public partial class SlotView : UserControl

{

    public static readonly DependencyProperty SlotStateProperty = DependencyProperty.Register(

        nameof(SlotState), typeof(SlotState), typeof(SlotView),

        new PropertyMetadata(SlotState.StandBy, OnSlotStateChanged));



    public SlotView()

    {

        InitializeComponent();

        UpdateForeground();

    }



    public SlotState SlotState

    {

        get => (SlotState)GetValue(SlotStateProperty);

        set => SetValue(SlotStateProperty, value);

    }



    private static void OnSlotStateChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)

        => ((SlotView)d).UpdateForeground();



    private void UpdateForeground()

    {

        Foreground = SlotState switch

        {

            var state when state.HasFlag(SlotState.Sender) && state.HasFlag(SlotState.Receiver) => Brushes.Violet,

            var state when state.HasFlag(SlotState.Sender) => Brushes.Tomato,

            var state when state.HasFlag(SlotState.Receiver) => Brushes.Lime,

            _ => Brushes.White,

        };

    }



    private void OnPointerPressed(object sender, MouseButtonEventArgs e)

    {

        if (DataContext is IWorkflowSlotViewModel context) context.SendConnectionCommand.Execute(null);

        e.Handled = true;

    }



    private void OnPointerReleased(object sender, MouseButtonEventArgs e)

    {

        if (DataContext is IWorkflowSlotViewModel context) context.ReceiveConnectionCommand.Execute(null);

        e.Handled = true;

    }

}

```
