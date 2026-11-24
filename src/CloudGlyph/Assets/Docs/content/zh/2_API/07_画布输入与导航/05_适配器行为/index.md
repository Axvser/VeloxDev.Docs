# 适配器行为

WPF 适配器用四个附着属性宿主闭合输入路由。它们解析命名部件、把原生手势翻译成模型命令，并发布模板绑定的渲染变换。其余六家适配器用自己的属性系统暴露同一组角色；下面的 WPF 签名是参照形状。

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

## WorkflowSurfaceBehavior

```csharp
public sealed class WorkflowSurfaceBehavior : DependencyObject
```

挂在宿主 `UserControl` 上。它把宿主的 `Focusable` 设为 `true`，注册一个 `SurfaceScrollerCore` 同时填 scroller 与 navigator，并拥有平移、Ctrl+滚轮缩放与滚轮归属。

### 附着属性

| 属性 | 类型 | 默认 | 含义 |
|---|---|---:|---|
| `IsEnabled` | `bool` | `false` | 打开表面。 |
| `ScrollViewerName` | `string?` | `null` | 要测量与滚动的命名 `ScrollViewer`。 |
| `CanvasName` | `string?` | `null` | 作为指针参照系的命名 `Canvas`。 |
| `GridDecoratorName` | `string?` | `null` | 命名 `IWorkflowGridDecorator`。 |
| `PointerPressSourceName` | `string?` | `null` | 接收按下事件的元素；空白画布平移从这里开始。 |
| `MinimapOverlayName` | `string?` | `null` | 命名 `IWorkflowMinimapOverlay`。 |
| `ZoomEnabled` | `bool` | `false` | 启用 Ctrl+滚轮缩放。 |
| `LinkMenuKey` | `string?` | `null` | 连线右键菜单的资源键。 |

### 访问器与方法

| 签名 | 说明 |
|---|---|
| `GetIsEnabled` / `SetIsEnabled(DependencyObject, bool)` | 读写 `IsEnabled`。 |
| `GetScrollViewerName` / `SetScrollViewerName` | 读写滚动视图名称。 |
| `GetCanvasName` / `SetCanvasName` | 读写画布名称。 |
| `GetGridDecoratorName` / `SetGridDecoratorName` | 读写装饰器名称。 |
| `GetPointerPressSourceName` / `SetPointerPressSourceName` | 读写按下源名称。 |
| `GetMinimapOverlayName` / `SetMinimapOverlayName` | 读写小地图名称。 |
| `GetZoomEnabled` / `SetZoomEnabled` | 读写缩放开关。 |
| `GetLinkMenuKey` / `SetLinkMenuKey` | 读写菜单资源键。 |
| `static Refresh(UserControl host)` | 重新解析命名部件并重新应用布局。替换内容或换树后调用。 |

缩放把 `Layout.Scale` 乘以 `1/1.1` 或 `1.1`，钳制在 `0.1`–`10`。平移通过 `WorkflowSurfaceMath.ClampScrollOffset` 与 `DefaultPanExtendRatio` 扩展画布。`GetPressHandle` 是 internal；拖动与连线行为用它尊重订阅者已否决的那一次按下。

## WorkflowCanvasTransformBehavior

```csharp
public static class WorkflowCanvasTransformBehavior
```

发布表面为节点与连线视图计算的变换。

| 成员 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `Transform` | `Transform?`（附着） | `null` | 当前渲染变换。 |
| `GetTransform(UIElement)` / `SetTransform(UIElement, Transform?)` | — | — | 附着访问器。 |

节点或连线模板把 `RenderTransform` 绑定到该属性。没有这个绑定，条目会按世界坐标渲染，忽略平移与缩放。`Apply` 是 internal；由表面写入。

## WorkflowNodeDragBehavior

```csharp
public sealed class WorkflowNodeDragBehavior : DependencyObject
```

挂在节点视图可拖动的部分。它挂接左键按下、移动、释放与丢失捕获，并跳过已经 `PreventDefault` 的按下。

| 属性 | 类型 | 默认 | 含义 |
|---|---|---|---|
| `IsEnabled` | `bool` | `false` | 为这个视图打开拖动。 |
| `CoordinateHostName` | `string?` | `null` | 用其坐标测量增量的画布。 |
| `CoordinateHostType` | `Type?` | `null` | 解析坐标宿主用的类型；回退到 `typeof(Canvas)`。 |

访问器是标准的三对：`GetIsEnabled`/`SetIsEnabled`、`GetCoordinateHostName`/`SetCoordinateHostName`、`GetCoordinateHostType`/`SetCoordinateHostType`。

没有坐标宿主时，行为使用最近的祖先 `Canvas`。

## WorkflowSlotConnectionBehavior

```csharp
public sealed class WorkflowSlotConnectionBehavior : DependencyObject
```

挂在插槽视图上。左键按下执行 `SendConnectionCommand`；左键释放执行 `ReceiveConnectionCommand`。控件的 `DataContext` 必须是 `ISlotComponent`。

| 属性 | 类型 | 默认 | 含义 |
|---|---|---:|---|
| `IsEnabled` | `bool` | `false` | 为这个视图打开连线手势。 |

访问器：`GetIsEnabled(DependencyObject)` 与 `SetIsEnabled(DependencyObject, bool)`。

已被表面否决的按下不会开始连线。连线拖动按设计不进撤销栈；进入历史的是它产生的结构编辑。

## 说明

- 所有名称都在 `UserControl` 的命名空间里解析。另一个命名空间里的部件找不到。
- `GridDecoratorName` 与 `MinimapOverlayName` 是可选钩子，供拥有那些覆盖层的功能使用。
- 部件在表面加载后才出现时，`Refresh` 是恢复路径。
