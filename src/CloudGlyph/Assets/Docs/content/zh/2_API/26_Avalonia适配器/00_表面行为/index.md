# 表面行为

`WorkflowSurfaceBehavior` 解析表面的命名部件、馈送视口、启动平移、挂接缩放、转发指针与键盘输入、打开连线菜单，并注册滚动/导航能力。Avalonia 版本使用附着 `AvaloniaProperty` 值，并以隧道方式处理滚轮。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.Avalonia`。

## WorkflowSurfaceBehavior

**签名：** `sealed class WorkflowSurfaceBehavior : AvaloniaObject`

### 附着属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 总开关。 |
| `ScrollViewerName` | `string?` | `null` | 其偏移定义度量视口的滚动容器。 |
| `CanvasName` | `string?` | `null` | 视图池填充的画布/面板。 |
| `GridDecoratorName` | `string?` | `null` | 实现 `IWorkflowGridDecorator` 的元素。 |
| `PointerPressSourceName` | `string?` | `null` | 空白区域按下开始平移的元素。 |
| `MinimapOverlayName` | `string?` | `null` | 实现 `IWorkflowMinimapOverlay` 的元素。 |
| `ZoomEnabled` | `bool` | `false` | 启用 Ctrl+滚轮缩放。 |
| `LinkMenuKey` | `string?` | `null` | 连线上下文菜单的资源键。 |

每个属性都是注册在 `UserControl` 上的 `AttachedProperty<T>`，并配有标准访问器，例如 `GetIsEnabled(AvaloniaObject)` / `SetIsEnabled(AvaloniaObject, bool)`、`GetScrollViewerName` / `SetScrollViewerName`。

`LinkMenuKey` 变化时会触发刷新，因为 XAML 属性顺序可能让它在 `IsEnabled` 之后写入。菜单是带键的 `ContextMenu`；适配器把按下的连线设为其 `DataContext`，打开它，并在打开期间挂起 `WorkflowInput`。

### 方法

| 方法 | 签名 | 说明 |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl host)` | 重新解析命名部件并重新绑定表面。 |

名称缺失会静默禁用该部件。

### 生命周期

- `IsEnabled = true` 挂载：解析名称、捕获已保存视口、安排一次恢复、从 `DataContext` 读取树、注册 `Scroller` / `Navigator` 并订阅。
- `IsEnabled = false` 摘除并停止写入模型。
- 适配器以 `RoutingStrategies.Tunnel` 注册滚轮处理器，因为 Avalonia 没有 `PreviewMouseWheel`；宿主只提供它想改变的决定。

```csharp
var scope = new NameScope();
NameScope.SetNameScope(host, scope);
scope.RegisterName("PART_ScrollViewer", scrollViewer);
scope.RegisterName("PART_Canvas", canvas);
scope.RegisterName("PART_SurfaceBorder", border);

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetPointerPressSourceName(host, "PART_SurfaceBorder");
WorkflowSurfaceBehavior.SetZoomEnabled(host, true);
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**预期结果：** 滚动会写入 `tree.GetHelper().Viewport`；摘除后的表面不再写入。
