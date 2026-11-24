# 托管视图

挂在 `Panel` 上的 `ViewPool` 消费可见集，为每个条目物化一个视图。它不是 `ItemsControl`：池维护自己的 active 表，在宿主的调度器上分批推进，并按运行时类型回收视图，而不是重建。

## 挂上池

```xml
<Canvas x:Name="PART_Canvas"
        Width="{Binding Layout.ActualSize.Width}"
        Height="{Binding Layout.ActualSize.Height}"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

| 附着属性 | 类型 | 含义 |
|---|---|---|
| `ItemsSource` | `INotifyCollectionChanged` | 可见集。绑定 `Helper.VisibleItems`，绝不绑 `tree.Nodes`。 |
| `TemplateSelector` | `DataTemplateSelector`（WPF） | 按运行时类型选模板。可选；不写时用面板自己的 `DataTemplates`。 |

任一属性变化都会销毁旧管线并重建，所以换源或换选择器不会留下旧的集合处理器。面板卸载时也会销毁系统。

## 选择器必须覆盖连线

`VisibleItems` 始终包含树的 `VirtualLink`，以及两端可见的真实连线。只处理 `INodeComponent` 的选择器对连线返回 `null`；池把 `null` 当作「这个运行时类型不支持」，并在系统生命周期内永久缓存这个结论。

```csharp
public sealed class WorkflowTemplateSelector : DataTemplateSelector
{
    public DataTemplate? NodeTemplate { get; set; }
    public DataTemplate? LinkTemplate { get; set; }

    public override DataTemplate? SelectTemplate(object item, DependencyObject container)
        => item switch
        {
            ILinkComponent => LinkTemplate,
            INodeComponent => NodeTemplate,
            _ => null,
        };
}
```

让连线模板同时处理真实与虚拟连线。虚拟连线的两个端点插槽没有挂到节点上；在连线拖动开始前，它的 `IsVisible` 是 `false`。把视图可见性绑到 `IsVisible` 就够了。

## 池对一个条目做什么

```mermaid
flowchart LR
    Add["可见集 Add"] --> Pending["pending 队列"]
    Pending --> Batch["调度器批次"]
    Batch --> Factory["Factory.WantsItem"]
    Factory --> Create["CreateView 或复用"]
    Create --> Activate["Activate（DataContext）"]
    Activate --> Attach["Attach（Children.Add）"]
    Attach --> Arrange["Arrange / SetZOrder"]
```

- 批次在适配器的调度器上排队，集合变化期间绝不内联执行。
- `Activate` 设置 `DataContext`，`Attach` 把视图加进宿主，`Arrange` 在命令式平台上写几何，`Measure` 是可选的钩子。
- 被移除的条目会先取消激活、摘除，再回池。超过 `MaxRecycledViewsPerType` 时销毁视图而不是隐藏；只隐藏会让宿主一直根住它。
- 失败条目报告 `Diagnostics.Failed(item, stage, exception)`，同批其余条目继续。

## 分批与默认策略

WPF 与另外五家走池的适配器默认使用 Core 的 `AdaptiveViewPoolPolicy`。初始每批 64 项、8 ms 帧预算，并根据实测吞吐与 pending 数量调整：

| Pending | 目标帧预算 |
|---|---|
| 大于 1024 | 16 ms |
| 大于 256 | 12 ms |
| 其它 | 8 ms |

批大小最多按 1.25× 增长、按 0.8× 收缩，带迟滞。`ViewPoolOptions` 暴露全部参数，`AdaptiveViewPoolPolicy.FromOptions(options)` 可以整体替换策略。想要固定策略的平台自己提供一个，就像 Avalonia 适配器的 `ViewPoolPolicy`。

契约是每帧至多一批：`IViewScheduler.Schedule` 必须投递，绝不能同步调用 batch。唯一例外是没有调度器的宿主（无句柄的 WinForms），此时实现内联执行，但把重入的下一批入队排空，而不是递归。

## 分层与连线覆盖层

Core 契约是五个窄层——`IViewFactory`、`IViewContainer`、`IViewArranger`、`IViewScheduler`、`IViewDiagnostics`——外加可选的 `IViewLayerPolicy`、`IViewLinkLayer`、`IViewMeasureHost`。`ViewSourcePipelineCore` 组合它们；适配器的 `ViewSourcePipeline` 闭合泛型参数。用覆盖层画连线的平台（MAUI）把 `LinkLayer.IsActive` 设为 `true` 并实现 `Handles`；这些条目永不进主池。

## 预期结果

- 四个可见节点在 `PART_Canvas` 下产生四个子视图，而不是图里每个节点一个。
- 滚动会移除离开节点的视图，并把它们复用给进入的节点；交给另一个节点的视图会收到新的 `DataContext`。
- 运行时换 `TemplateSelector` 只重建一次池，不会挂上第二个 detach 处理器。
- 选择器没有连线模板时，往 `VisibleItems` 里加连线不会产生视图，也不会重复抛异常；不支持的类型被缓存。

## 下一页

[验证](../03_验证/index.md)把 Helper 与池放进一个可运行示例。
