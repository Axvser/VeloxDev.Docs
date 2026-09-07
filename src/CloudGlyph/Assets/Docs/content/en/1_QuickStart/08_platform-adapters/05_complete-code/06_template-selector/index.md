# Platform Adapters - `TemplateSelector.cs`

Exact output of `dotnet new wpf-v-selector -n TemplateSelector -ns Demo.Views.Workflow`. A `DataTemplateSelector` that maps the four workflow view-model interfaces (`IWorkflowLinkViewModel`, `IWorkflowSlotViewModel`, `IWorkflowNodeViewModel`, `IWorkflowTreeViewModel`) to the templates you assign in the host's resources.

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using VeloxDev.WorkflowSystem;

namespace Demo.Views.Workflow;

/// <summary>
/// Assign the four DataTemplate properties in XAML resources, then use this
/// selector with behaviors:ViewPool.TemplateSelector or another items host.
/// </summary>
public sealed class TemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }

    public DataTemplate? SlotTemplate { get; set; }

    public DataTemplate? LinkTemplate { get; set; }

    public DataTemplate? TreeTemplate { get; set; }

    public override DataTemplate SelectTemplate(object item, DependencyObject container)
        => item switch
        {
            IWorkflowLinkViewModel => LinkTemplate
                ?? throw new InvalidOperationException("LinkTemplate is not set."),
            IWorkflowSlotViewModel => SlotTemplate
                ?? throw new InvalidOperationException("SlotTemplate is not set."),
            IWorkflowNodeViewModel => NodeTemplate
                ?? throw new InvalidOperationException("NodeTemplate is not set."),
            IWorkflowTreeViewModel => TreeTemplate
                ?? throw new InvalidOperationException("TreeTemplate is not set."),
            _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
        };
}
```
