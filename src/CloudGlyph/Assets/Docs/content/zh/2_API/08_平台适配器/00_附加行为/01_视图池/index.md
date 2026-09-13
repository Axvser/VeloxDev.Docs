# API — 附加行为 · ViewPool 与 ViewManager

`ViewPool` + `ViewManager` 为工作流表面提供对象池视图虚拟化：条目进出绑定的集合时，管理器为每个条目物化一个视图、按类型复用池中视图，并隐藏被移除的条目。

## 类：`ViewPool`

把容器变成虚拟化宿主的附加对象池支持。在 XAML 风格适配器上是附加属性持有类；在 Razor 上是组件；在 WinForms 上是以 `Control` 为键的静态持有类。

| 适配器 | 形态 | `ItemsSource`（类型） | `TemplateSelector`（类型） |
|---|---|---|---|
| WPF | `sealed class : DependencyObject` | 附加 `INotifyCollectionChanged?` | 附加 `DataTemplateSelector?` |
| Avalonia | `sealed class : AvaloniaObject` | `INotifyCollectionChanged?` | `IDataTemplate?` |
| WinUI | `sealed class : DependencyObject` | `INotifyCollectionChanged?` | `DataTemplateSelector?` |
| MAUI | `sealed class` | `BindableProperty` `INotifyCollectionChanged?` | `DataTemplateSelector?` |
| WinForms | `sealed class` | 静态 `SetItemsSource(Control, INotifyCollectionChanged?)` | 静态 `SetTemplateSelector(Control, IWorkflowTemplateSelector?)` |
| Jalium | `public static class` | 附加 `INotifyCollectionChanged?` | 附加 `IWorkflowTemplateSelector?` |

成员遵循附加属性约定 `GetItemsSource(container)` / `SetItemsSource(container, value)`（`TemplateSelector` 同理）；WPF 的 XML 注释展示了预期的 XAML 用法：

```xml
<ScrollViewer>
    <Canvas behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}" />
</ScrollViewer>
```

`ItemsSource` 改变时（WPF/Avalonia/WinUI/MAUI）池为该容器创建一个 `ViewManager`、将其挂到集合上，并在 `Unloaded` / 旧值替换时清理。**Jalium** 还额外暴露 `internal static void UpdateRenderTransforms(Panel panel, Transform transform)`，把表面的画布变换镜像到池化视图。

## 类：`ViewManager`

由 `ViewPool` 创建、按容器密封的管理器。它按条目 `Type` 用 `Queue` 池化视图，维护活动视图加待处理批次，订阅集合变化 / 条目属性变化并渲染。

| 适配器 | 构造 / 工厂 | 额外公共成员 |
|---|---|---|
| WPF | `ViewManager(Panel panel)` | `void Attach(INotifyCollectionChanged)`；`void Detach()` |
| Avalonia | `ViewManager(Panel panel, IDataTemplate? templateSelector = null)` | `void Attach(INotifyCollectionChanged)`；`void Detach()` |
| WinUI | `ViewManager(Panel panel)` | `void SetTemplateSelector(DataTemplateSelector?)`；`void Attach(INotifyCollectionChanged)`；`void Detach()` |
| MAUI | `ViewManager(Layout layout)` | `void Attach(INotifyCollectionChanged)`；`void Detach()` |
| WinForms | `ViewManager(Control host)`（`: IDisposable`） | `void SetTemplateSelector(IWorkflowTemplateSelector)`；`void Attach(INotifyCollectionChanged)`；`void Detach()`；`void Dispose()` |
| Jalium | `ViewManager(Panel host)`（`: IDisposable`） | `void SetTemplateSelector(IWorkflowTemplateSelector)`；`void Attach(INotifyCollectionChanged)`；`void Detach()`；`void Dispose()` |

**渲染（已验证，WPF）：** 按每个 dispatcher `Background` 滴答 **3** 个一批渲染视图。被移除项折叠为 `Visibility.Collapsed`、解绑并归还池。模板查找顺序：`ViewPool.TemplateSelector` → 容器资源树 → `Application.Current.Resources`。其它适配器实现相同的批处理语义；是否逐字复用同样的批次大小属 `*推断所得*`。

**Avalonia 说明：** 提供模板选择器时使用 `IDataTemplate.Match(context)`；否则按条目类型找模板。

## 接口：`IWorkflowTemplateSelector`

WinForms 与 Jalium 用一个小工厂契约（命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`）替代 XAML 的 `DataTemplateSelector` / `IDataTemplate`。WinForms 在 `ViewManager.cs` 中声明；Jalium 在独立文件中声明。

| 适配器 | 签名 |
|---|---|
| WinForms | `Control CreateView(object item)` |
| Jalium | `FrameworkElement CreateView(object item)` |

## Razor 组件：`ViewPool`

`ViewPool.razor` + 代码后置（`partial class ViewPool : ComponentBase`）：

| 参数 | 类型 | 说明 |
|---|---|---|
| `ItemsSource` | `IEnumerable?` | 要渲染的条目。 |
| `ItemTemplate` | `RenderFragment<object>?` | 每条内容。 |
| `EmptyContent` | `RenderFragment?` | 源为空时渲染。 |
| `KeySelector` | `Func<object, object>?` | 池化 / 标识键。 |
