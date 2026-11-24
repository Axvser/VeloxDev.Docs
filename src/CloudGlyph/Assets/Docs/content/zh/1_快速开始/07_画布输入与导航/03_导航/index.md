# 导航

导航分两半。**手势**移动表面：在空白画布上左键拖动平移，`Ctrl` + 滚轮缩放，两者都走滚动容器。**能力**把表面移到目标：`IWorkflowSurfaceNavigator.CenterOn` 与 `Locate()` 扩展。两者都是已挂载适配器注册的可选能力，所以宿主调用时不需要知道平台。

## 内置手势

| 手势 | 发生什么 | 实现在哪 |
|---|---|---|
| 空白画布左键拖动 | 通过写滚动偏移实现平移。被订阅者否决的按下不会起平移。 | `WorkflowSurfaceBehavior` |
| `Ctrl` + 滚轮 | 围绕视口中心缩放。一格把 `Layout.Scale` 乘 `1/1.1`（向上）或 `1.1`（向下），夹在 `0.1`–`10`。 | `WorkflowSurfaceBehavior`（`ZoomEnabled="True"`） |
| 普通滚轮 | 纵向滚动，步长用平台自己的。WPF 一格是 `WheelScrollLines × 16` px（默认 3 行时 48 px）。 | `WorkflowSurfaceBehavior` |
| 滚轮在兄弟控件上 | 不滚画布。 | `WorkflowSurfaceBehavior` |

缩放枢轴是视口中心下方的世界点。适配器先捕获这个点，改变缩放，缩放把内容拉过原点时扩大画布覆盖，再滚动让捕获点留在中心。缩放期间节点几何不动，只有滚动在动。

## 定位一个组件

`WorkflowNavigationEx` 给节点、插槽、连线加上 `Locate()`。它从**模型数据**把元素换算成画布局部点，再请 navigator 居中：

| 目标 | 使用的点 |
|---|---|
| `INodeComponent` | 节点矩形的中心。 |
| `ISlotComponent` | 父节点矩形的中心，不读插槽自己的 `Anchor`。 |
| `ILinkComponent` | 两端节点矩形中心的中点，不读已发布的曲线。 |

因为不涉及测量或绘制，屏幕外的节点、还没测量的插槽在拥有视图之前就能被定位。没有挂表面 navigator，或目标没有有限坐标时，调用返回 `false` 且不改变任何东西。

```csharp
using VeloxDev.WorkflowSystem.StandardEx;

// Pan only: the current zoom is preserved.
bool moved = node.Locate();
bool slotMoved = slot.Locate();
bool linkMoved = link.Locate();
```

目标在当前可滚范围内放不到中心时，WPF 表面会按缺口撑大画布，再重新居中。WinForms 的平移引擎接受有符号目标，没有 extent 上限。

## 两项能力

已挂载的适配器会在树的路由上注册两个对象：

```csharp
var input = WorkflowInput.For(tree);

// Turn a wheel delta into this platform's scroll.
input.Scroller?.ScrollBy(wheelDeltaX, wheelDeltaY);

// Put a canvas-local point at the viewport centre.
input.Navigator?.CenterOn(localX, localY);
```

两者在适配器注册之前都是 `null`，卸载时清空。宿主把它们当作可选能力。

`SurfaceScrollerCore` 是这两个接口的 Core 实现。适配器提供一个窄的 `ISurfaceScrollHost`——偏移、范围、视口尺寸、滚轮配置、`ApplyOffset` 与 `ExpandCanvas`——算术只写一次：

- 某一轴增量为零时，该轴不动。
- 横向正方向是「向右」，纵向正方向是「远离用户」；它们不是同一个物理方向，所以 `ScrollBy` 在纵轴上做减，而把一根轴映射到另一根轴的调用方要自己取反。
- 越界时按 `WorkflowSurfaceMath.DefaultPanExtendRatio`（`0.15`）撑大画布，而不是停在边缘；宿主采纳新范围后重新读最大值。
- `CenterOn` 用 `WorkflowSurfaceMath.CenterScroll`，目标无法居中时按精确差额撑大画布。

## 预期结果

- 左键拖动空白画布时所有节点与连线一起移动；状态栏的缩放文本不变。
- `Ctrl` + 滚轮围绕视口中心下方的点缩放，不是围绕世界原点。
- 调用 `node.Locate()` 在当前缩放下把该节点滚到中心。
- 对远在当前范围外的节点调用 `Locate()` 会撑大画布，仍然居中。

## 下一页

[验证](../04_验证/index.md)端到端运行这些行为，并给出完整代码。
