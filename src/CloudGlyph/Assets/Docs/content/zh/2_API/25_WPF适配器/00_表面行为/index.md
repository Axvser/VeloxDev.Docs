# 表面行为

`WorkflowSurfaceBehavior` 解析表面的命名部件、馈送视口、启动平移、挂接缩放、转发指针与键盘输入、打开连线菜单，并注册滚动/导航能力。它是静态附着属性类；状态存放在宿主元素上。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WPF`。

## WorkflowSurfaceBehavior

**签名：** `sealed class WorkflowSurfaceBehavior : DependencyObject`

### 附着属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 总开关；只有为 `true` 时其他属性才被读取。 |
| `ScrollViewerName` | `string?` | `null` | 其偏移定义度量视口的滚动容器。 |
| `CanvasName` | `string?` | `null` | 视图池填充的画布/面板。 |
| `GridDecoratorName` | `string?` | `null` | 实现 `IWorkflowGridDecorator` 的元素。 |
| `PointerPressSourceName` | `string?` | `null` | 空白区域按下开始平移的元素。 |
| `MinimapOverlayName` | `string?` | `null` | 实现 `IWorkflowMinimapOverlay` 的元素。 |
| `ZoomEnabled` | `bool` | `false` | 启用 Ctrl+滚轮缩放。 |
| `LinkMenuKey` | `string?` | `null` | 连线上下文菜单的资源键，在资源字典存在后解析。 |

每个属性都有标准访问器，例如 `GetIsEnabled(DependencyObject)` / `SetIsEnabled(DependencyObject, bool)`、`GetScrollViewerName` / `SetScrollViewerName`，八个属性皆是如此。

`LinkMenuKey` 是键而不是菜单本身，因为该属性位于表面根元素，此处的 `{StaticResource}` 会在定义菜单的字典之前解析。适配器在打开前把按下的连线设为菜单的 `DataContext`，打开期间挂起 `WorkflowInput`，关闭时恢复。

### 方法

| 方法 | 签名 | 说明 |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl host)` | 重新解析命名部件并重新绑定表面。替换模板或重新承载表面后调用。 |

名称缺失会静默禁用该部件：没有异常也没有日志，因此“表面什么也不做”通常是名称拼写错误。

### 生命周期

- `IsEnabled = true` 挂载：解析名称、捕获树的已保存视口、安排一次恢复、从 `DataContext` 读取树、注册 `Scroller` / `Navigator`，并订阅树及其 Helper。
- `IsEnabled = false` 摘除：停止写入模型、清空能力、取消订阅。
- `DataContext` 变化时重新绑定新的 `ITreeComponent`。
- 适配器通过 `UserControl` 的 NameScope 解析 `PART_*`，而不是可视树。代码构建的表面必须先注册名称。

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

**预期结果：** 滚动 `ScrollViewer` 会写入 `tree.GetHelper().Viewport`；摘除后的表面不再写入。
