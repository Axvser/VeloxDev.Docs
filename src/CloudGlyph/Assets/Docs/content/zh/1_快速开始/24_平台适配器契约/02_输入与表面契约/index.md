# 输入与表面契约

表面不是一堆按平台各写一遍的手势，而是 Core 里的几个对象：一条输入路由、两个滚动能力接口、网格/装饰器/小地图的数据交换，以及一套视图池组合。适配器实现接口，宿主调用路由与能力。

## 输入路由

`WorkflowInput` 一棵树一个实例。适配器为每个动作只创建一个参数对象并调用 `Route`；路由把它交给目标，再逐级上溯到祖先，最后到树。每个订阅者看到的是**同一个**参数对象与**同一个** `WorkflowEventHandle`。

```csharp
var input = WorkflowInput.For(tree);          // 一棵树一个实例
input.Route(pointerArgs);                     // 适配器每个动作调用一次
input.Route(keyArgs);                         // 键只冒泡；Core 没有默认按键动作

if (tree.GetHelper() is IInputEvents events)  // 组件这样订阅
{
    events.Input.PointerEntered += (_, e) => Console.WriteLine(e.Target?.GetType().Name);
}
```

| 成员 | 含义 |
|---|---|
| `PointerTarget` / `HoveredLink` | 指针所在的组件或连线；空白画布上为 `null` |
| `ConnectionSender` / `PreviewReceiver` / `PreviewState` / `PreviewCheck` | 连接拖拽的实时预览 |
| `PreviewChanged` / `PreviewValidating` | 预览快照，以及「只否决这一次拖拽的候选」的机会 |
| `HitRadius` | 连线命中的触及半径；默认取 `LinkHitTestEx.DefaultHitRadius`（6） |
| `IsSuspended` | 弹窗打开期间暂停悬停记账 |
| `Scroller` / `Navigator` | 适配器挂载期间注册的能力；两者都可为 `null` |

**预期结果：** 订阅树的 `Input.KeyDown`，无论指针在哪都能收到按键 —— 树是每条路由的最后一级。

## 滚动与导航能力

适配器拥有平台的滚轮，并在挂载期间把两个接口注册到路由上。

```csharp
// IWorkflowSurfaceScroller
input.Scroller?.ScrollBy(deltaX, deltaY);

// IWorkflowSurfaceNavigator
input.Navigator?.CenterOn(localX, localY);
```

`ScrollBy` 接收的是**滚轮增量**，不是滚动偏移。X 为正表示朝右侧内容移动；Y 为正表示朝上方内容移动。某个轴为 0 时该轴不动。`CenterOn` 接收画布局部坐标，把它放到视口中心；Core 的 `WorkflowNavigationEx` 负责从组件算出这个点：

```csharp
using VeloxDev.WorkflowSystem.StandardEx;

node.Locate();   // 节点矩形的中心
slot.Locate();   // 所属节点的中心
link.Locate();   // 两端节点中心的中点
```

`Locate()` 只读模型数据，所以尚未测量或在屏幕外的元素也能到达中心。它只平移，不缩放。

**预期结果：** 表面挂载后 `Scroller` 非空，卸载后恢复为 `null`；`ScrollBy(0, 0)` 不改变任何东西。

## 网格、小地图与度量

表面每一轮把同一组数字推给两个 Core 接口。

| 接口 | 表面推入的成员 |
|---|---|
| `IWorkflowGridDecorator` | `ScrollOffsetX`、`ScrollOffsetY`、`ContentOffsetX`、`ContentOffsetY`；读取 `RulerBand` |
| `IWorkflowMinimapOverlay` | 以上全部，外加 `ViewportWidth`、`ViewportHeight`、`WorkflowTree`、`IsMinimapVisible`、`AvailableRight/Top/Bottom`、`MinimapMargin` |

`RulerBand` 是唯一一个不只影响绘制的值：表面会把它转给虚拟化器，避免浮在顶/左侧标尺下面的节点被判为不可见。

`SurfaceMetrics.Create` 从表面尺寸、标尺带与可见滚动条推导出覆盖层可用的角落。`SurfaceViewport` 是滚动/内容偏移与视口尺寸的不可变快照；`SurfaceCanvas` 是传给内容片段的计算画布尺寸。

**预期结果：** 滚动之后，装饰器的 `ScrollOffsetX` 与树的 `Viewport.Horizontal` 一起移动。

## 视口恢复

`SurfaceViewportRestoreCore` 拥有保存/恢复状态机。在表面写入自己的第一份视口**之前**捕获树的保存位置，然后排一次延迟恢复：

```csharp
var restore = new SurfaceViewportRestoreCore();
restore.Capture(tree);                 // 每棵树只读一次 Layout.ViewportOffset
restore.Schedule(host);                // 宿主延迟并应用；每棵树恢复一次
```

捕获以树实例为键，所以反复刷新不会把用户拽回原位。适配器尚未就绪时，待恢复位置会保留，下一轮表面刷新再试。

**预期结果：** 带有非零 `Layout.ViewportOffset` 的树从该位置打开；没有保存位置的树停在原点。

## 视图池组合

适配器把 `ViewSourcePipelineCore` 闭合一次，暴露用户看到的短类型。Core 类型有九个类型参数 —— 宿主、视图、条目、优先级、工厂、容器、排列器、调度器、诊断 —— 并由它们构造池。

```csharp
public sealed class ViewPool : INotifyCollectionChangedSource
{
    // 适配器的组合点；用户只设置 ItemsSource 与 TemplateSelector。
}
```

池的边界是策略，不是平台代码：

| `IViewPoolPolicy` 成员 | 含义 |
|---|---|
| `BatchSize` | 一个物化批次最多创建多少个视图 |
| `FrameBudgetMilliseconds` | 一个批次的墙钟预算；0 或负值表示不限 |
| `MaxRecycledViewsPerType` | 每个运行时类型保留多少回收视图；0 或负值表示不限 |

`AdaptiveViewPoolPolicy()` 从 64 个视图、8 ms 预算起步，再按实测吞吐调整。凡是用池的适配器都以它为默认。

**预期结果：** 池为每个可见项创建一个视图，按运行时类型回收，并把停用的视图以 `Visibility.Collapsed` 留在面板上，而不是摘掉。
