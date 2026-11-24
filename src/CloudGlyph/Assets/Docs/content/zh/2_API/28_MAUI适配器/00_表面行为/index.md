# 表面行为

`WorkflowSurfaceBehavior` 解析命名部件、馈送视口、拥有平移/捏合手势与 Windows 滚轮钩子、路由输入、打开连线菜单，并注册滚动/导航能力。MAUI 没有渲染变换载体；表面与视图排列器拥有几何。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.MAUI`。

## WorkflowSurfaceBehavior

**签名：** `sealed class WorkflowSurfaceBehavior`（静态附着属性类，不继承 `BindableObject`）

### 附着属性

| 属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `IsEnabled` | `bool` | `false` | 总开关。 |
| `ScrollViewerName` | `string?` | `null` | 其偏移定义度量视口的 `ScrollView`。 |
| `CanvasName` | `string?` | `null` | 视图池填充的 `AbsoluteLayout`。 |
| `GridDecoratorName` | `string?` | `null` | 实现 `IWorkflowGridDecorator` 的元素。 |
| `PointerPressSourceName` | `string?` | `null` | 空白区域按下开始平移的元素。 |
| `MinimapOverlayName` | `string?` | `null` | 实现 `IWorkflowMinimapOverlay` 的元素。 |
| `ZoomEnabled` | `bool` | `false` | 启用捏合与 Ctrl+滚轮缩放。 |
| `LinkMenuKey` | `string?` | `null` | 连线 `MenuFlyout` 的资源键。 |

访问器为标准静态方法对，接收 `BindableObject`，例如 `GetIsEnabled` / `SetIsEnabled`、`GetScrollViewerName` / `SetScrollViewerName`。

`MenuFlyout` 没有 `DataContext`，因此适配器把按下的连线喂给每个 `MenuFlyoutItem.DataContext`。Windows 上打开原生浮出层；其他平台自行物化一个由 `Margin` 定位的覆盖层。

### 方法

| 方法 | 签名 | 说明 |
| --- | --- | --- |
| `Refresh` | `static void Refresh(ContentView host)` | 重新解析命名部件并重新绑定表面。 |
| `RequestViewportRestore` | `static void RequestViewportRestore(ContentView host, double viewportX, double viewportY)` | 把画布局部位置写入 `Layout.ViewportOffset`，用新的 `SurfaceViewportRestoreCore` 捕获，并刷新以便下次布局恢复。`IsEnabled` 为 false 时忽略。 |

`RequestViewportRestore` 在宿主为 null 时抛 `ArgumentNullException`。这是 MAUI 专属的显式恢复入口；普通挂载路径会自行捕获已保存视口。

### 手势

- **平移**使用 `PanGestureRecognizer`，Windows 上另有原生指针处理。
- **缩放**触摸时使用 `PinchGestureRecognizer`，并配有 `#if WINDOWS` 滚轮钩子。
- 适配器把 Windows `ScrollViewer.ManipulationMode` 设为 `None`，使其程序化的 `ChangeView` 成为唯一滚动驱动；不要改这个值。
- 连接拖拽期间的候选接收端由插槽连接行为报告，而不是表面，因为视口尺寸的覆盖层无法靠视觉命中回答“是哪个插槽”。

```csharp
public partial class TreeView : ContentView
{
    public TreeView()
    {
        InitializeComponent();
        BindingContextChanged += (_, _) => WorkflowSurfaceBehavior.Refresh(this);
    }
}
```

**预期结果：** 表面在 `BindingContextChanged` 时订阅，执行平移与缩放并写入视口；摘除后的表面停止写入。
