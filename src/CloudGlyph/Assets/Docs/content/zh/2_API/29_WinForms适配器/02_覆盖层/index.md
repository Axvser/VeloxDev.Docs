# 覆盖层

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`；滚动源接口在 `VeloxDev.WorkflowSystem.Platform`。

## 类：WorkflowMinimapOverlay

`public class WorkflowMinimapOverlay : VisualElement, IWorkflowMinimapOverlay, IWorkflowMinimapScrollSource`

整面缩略图层。只有缩略图矩形可命中，其余部分让指针输入穿过。树订阅、映射、放置与拖拽数学在 Core 的 `MinimapPipeline`；本类提供调色板、绘制与指针处理器。

### 构造函数

`public WorkflowMinimapOverlay()`

把覆盖层创建为整面图层，并创建 `MinimapPipeline` 与输入宿主。

### 事件

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ViewportScrollRequested` | `event Action<double, double>?` | 拖拽视口块时请求的世界原点。 |

### 属性

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `MinimapBackground` | `Color` | `#331E1E1E` | 面板填充。 |
| `MinimapBorderBrush` | `Color` | `#DC94A3B8` | 面板边框。 |
| `NodeBrush` | `Color` | `#DC38BDF8` | 每个节点的缩略图填充。 |
| `ViewportStroke` | `Color` | `#F0FFFFFF` | 视口块描边。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` | 表面推入的滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` | 表面推入的内容偏移。 |
| `RulerBand` | `double` | `0` | 恒为零：小地图不预留标尺带。 |
| `ViewportWidth` / `ViewportHeight` | `double` | `1` | 可见视口尺寸。 |
| `WorkflowTree` | `ITreeComponent?` | `null` | 小地图渲染的树。 |
| `IsMinimapVisible` | `bool` | `true` | 是否绘制并命中。 |
| `MinimapWidth` / `MinimapHeight` | `double` | `200` / `140` | 请求的缩略图尺寸（表面像素）。 |
| `MinimapMargin` | `double` | `12` | 与可用角的间距。 |
| `AvailableRight` / `AvailableTop` / `AvailableBottom` | `double` | `0` | 表面推入的角落排除量。 |

### 扩展点

`protected virtual void DrawMinimap(Graphics graphics, MinimapDrawContext context)` 绘制默认面板。重写并调用 `base` 可在其上追加。`protected static Color ParseColor(string hex)` 接受 `#RRGGBB`、`#AARRGGBB` 与颜色名。

### 备注

- 实现 `IWorkflowMinimapOverlay`，表面因此无需知道具体类型就能推送度量。
- `IWorkflowMinimapScrollSource` 由适配器声明：事件携带屏幕空间滚动量，只有自带滚动模型的宿主才能消费。

## 类：WorkflowInfoOverlay

`public sealed class WorkflowInfoOverlay : VisualElement`

实时画布信息 HUD。表面推入偏移与缩放；HUD 从树读取实际尺寸与可见计数。

### 构造函数

`public WorkflowInfoOverlay()`

创建 HUD、复制按钮与模型订阅。文本区域对命中透明。

### 属性

| 属性字段 | CLR 类型 | 默认值 |
| --- | --- | --- |
| `ScrollOffsetXProperty` | `double` | `0` |
| `ScrollOffsetYProperty` | `double` | `0` |
| `ContentOffsetXProperty` | `double` | `0` |
| `ContentOffsetYProperty` | `double` | `0` |
| `ZoomProperty` | `double` | `1` |

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `CopyButton` | `VisualButton` | 唯一可交互区域；宿主可改样式。 |
| `CopyFeedback` | `event EventHandler<string>?` | 复制尝试后带一条短状态触发。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 表面像素中的水平/垂直滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 内容偏移（布局原点加标尺带）。 |
| `Zoom` | `double` | 相机缩放。 |
| `Lines` | `IReadOnlyList<string>` | 当前显示的行，按显示顺序。 |

### 示例

```csharp
var info = new WorkflowInfoOverlay { Zoom = 1.25 };
info.CopyFeedback += (_, message) => statusLabel.Text = message;
// Source: source
```

复制会用平台换行连接 `Lines`。剪贴板失败通过 `CopyFeedback` 报告，不抛异常。

## 接口：IWorkflowMinimapScrollSource

`public interface IWorkflowMinimapScrollSource` —— 命名空间 `VeloxDev.WorkflowSystem.Platform`。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ViewportScrollRequested` | `event Action<double, double>?` | 拖拽小地图视口时请求的世界原点。 |

它被排除在 `IWorkflowMinimapOverlay` 之外，以保持共享的 Core 接口与框架无关。
