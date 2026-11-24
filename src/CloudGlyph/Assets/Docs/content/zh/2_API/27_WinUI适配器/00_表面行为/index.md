# 表面行为

`WorkflowSurfaceBehavior` 解析表面的命名部件、馈送视口、启动平移、挂接缩放、转发指针与键盘输入、打开连线菜单，并注册滚动/导航能力。WinUI 没有预览指针阶段，因此滚轮以 `handledEventsToo: true` 在画布上接管，平移用组合平移移动画布而不是绑定渲染变换。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`，程序集 `VeloxDev.WinUI`。

## WorkflowSurfaceBehavior

**签名：** `sealed class WorkflowSurfaceBehavior : DependencyObject`

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
| `LinkMenuKey` | `string?` | `null` | 连线 `MenuFlyout` 的资源键。 |

访问器为标准静态方法对，例如 `GetIsEnabled(DependencyObject)` / `SetIsEnabled(DependencyObject, bool)`、`GetScrollViewerName` / `SetScrollViewerName`。

`MenuFlyout` 没有 `DataContext`，因此适配器把按下的连线喂给每个 `MenuFlyoutItem.DataContext`。适配器在浮出层打开期间同样挂起 `WorkflowInput`。

### 方法

| 方法 | 签名 | 说明 |
| --- | --- | --- |
| `Refresh` | `static void Refresh(UserControl host)` | 重新解析命名部件并重新绑定表面。 |

名称缺失会静默禁用该部件。请在 `Loaded` 之后或模板更换后调用 `Refresh`；此时 name scope 已就绪。

### 平移

WinUI 子元素不绑定渲染变换。表面把平移作为画布上的组合平移（`state.Canvas.Translation`）应用。因此自定义连线视图必须把同一个 `ActualOffset` 烘焙进几何，并把自身放在负偏移处；demo 这一对的下一页展示了该帧。

```csharp
public sealed partial class WorkflowSurface : UserControl
{
    public WorkflowSurface()
    {
        InitializeComponent();
        DataContext = new TreeViewModel();
        Loaded += (_, _) => WorkflowSurfaceBehavior.Refresh(this);
    }
}
```

**预期结果：** 平移与缩放移动整块画布，视口被发布；摘除后的表面停止写入模型。
