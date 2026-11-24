# 适配器视图池

WPF 适配器用一个附着行为与一个管线类闭合 Core 契约。宿主使用的是附着行为；管线与层类公开，供自行组合池的宿主使用。

命名空间：附着行为在 `VeloxDev.WorkflowSystem.AttachedBehaviors`，管线与层在 `VeloxDev.WorkflowSystem.ViewHosting`。

## ViewPool（附着行为）

```csharp
public sealed class ViewPool : DependencyObject
```

挂在 `Panel`（例如 `PART_Canvas`）上。每个面板恰好得到一个管线，保存在 `ConditionalWeakTable` 中。

### 附着属性

| 属性 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | 可见集。绑定 `Helper.VisibleItems`，绝不要绑 `tree.Nodes`。 |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | 按运行时类型选择模板；缺省时使用面板自己的 `DataTemplates`。 |

| 访问器 | 说明 |
|---|---|
| `GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)` | 读写来源。 |
| `GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, DataTemplateSelector?)` | 读写选择器。 |

任一属性变化都会销毁旧管线并重建。面板卸载时同样销毁。

用法：

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

## ViewSourcePipeline

```csharp
public sealed class ViewSourcePipeline
    : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent,
        DispatcherPriority, ViewFactory, ViewContainer, ViewArranger,
        ViewScheduler, ViewDiagnostics>
```

| 签名 | 说明 |
|---|---|
| `ViewSourcePipeline(Panel panel, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | 组合 WPF 各层并启动池。`poolPolicy` 默认 `new AdaptiveViewPoolPolicy()`（初始 64、8 ms）。 |

继承成员：`Pool`（`ViewPool<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority>`）、`Dispose()` 以及全部 `IViewHost` 层属性。

## 层类

都在 `VeloxDev.WorkflowSystem.ViewHosting`，均为 `public sealed`。

### ViewFactory

```csharp
public ViewFactory(Panel panel, DataTemplateSelector? templateSelector);
public bool WantsItem(IWorkflowComponent item);      // 恒为 true
public FrameworkElement? CreateView(IWorkflowComponent item);
```

依次通过选择器、面板可视化树资源、应用程序资源解析模板。选择按运行时类型缓存；没有匹配时返回 `null`。

### ViewContainer

```csharp
public void Attach(Panel host, FrameworkElement view);      // 加入 Children，幂等
public void Detach(Panel host, FrameworkElement view);      // 空操作
public void Activate(FrameworkElement view, IWorkflowComponent item); // DataContext + Visible
public void Deactivate(FrameworkElement view);              // 清空 DataContext + Collapsed
public void SetZOrder(FrameworkElement view, int zIndex);   // 空操作；模板绑定 ZIndex
public void Destroy(Panel host, FrameworkElement view);     // 从 Children 移除
```

### ViewArranger

```csharp
public void Arrange(FrameworkElement view, IWorkflowComponent item); // 空操作
```

WPF 模板通过绑定拥有几何。

### ViewScheduler

```csharp
public ViewScheduler(Dispatcher dispatcher);
public DispatcherPriority BatchPriority => DispatcherPriority.Background;
public bool Schedule(Action batch, DispatcherPriority priority); // Dispatcher.BeginInvoke
```

每次接受的投递都返回 `true`。dispatcher 为 null 时抛 `ArgumentNullException`。

### ViewDiagnostics

```csharp
public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception);
```

把 `[ViewDiagnostics] {stage} failed for {type|batch}: {exception}` 写到调试输出。

### ViewLayerPolicy

```csharp
public int GetZOrder(IWorkflowComponent item); // 恒为 0
```

### ViewLinkLayer

```csharp
public bool IsActive => false;
public bool Handles(IWorkflowComponent item) => false;
public void Render(Panel host, IReadOnlyList<IWorkflowComponent> items); // 空操作
```

WPF 每条连线使用一个池化视图，所以链接层不激活。

### ViewMeasureHost

```csharp
public void Measure(Panel host, FrameworkElement view, IWorkflowComponent item); // 空操作
```

## 说明

- 选择器必须覆盖连线。`VisibleItems` 始终包含虚拟连线；只处理节点的选择器会把连线类型缓存为「不支持」。
- 视图交给另一个项时会收到新的 `DataContext`；视图的身份不是项的身份。
- 集合变化期间池绝不会就地执行批次；调度器是线程边界。
