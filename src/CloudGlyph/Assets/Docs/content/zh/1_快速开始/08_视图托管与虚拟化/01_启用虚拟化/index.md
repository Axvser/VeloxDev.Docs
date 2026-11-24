# 启用虚拟化

虚拟化是 Helper 的属性，不是树的属性。用格子尺寸构造的 Helper 会安装空间映射并维护可见集；无参构造的 Helper 全量渲染，`VisibleItems` 永远不更新。

## 选 Helper

```csharp
using VeloxDev.WorkflowSystem;

// Virtualization off. VisibleItems stays empty.
public sealed class PlainHelper : TreeHelper { }

// Virtualization on. The cell size is the spatial grid's cell, in canvas units.
internal sealed class VirtualizeHelper : TreeHelper
{
    public VirtualizeHelper() : base(200) { }
}
```

生成器通过树特性选择 Helper：

```csharp
[WorkflowBuilder.Tree<VirtualizeHelper>]
internal partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}
```

`TreeHelper(double)` 还会在 `TreeHelper` tick 通道尚未运行时把它按 10 fps 启动。tick 只检查一个脏标志；它自己的线程上不做可见集工作。

## 可见集里有什么

`Helper.VisibleItems` 是由 `WorkflowSpatialEx.VirtualizeCore` 维护的 `ObservableCollection<IWorkflowComponent>`。它包含：

- 树的 `VirtualLink`（始终包含，让拖动预览有视图），
- 空间查询返回的每个节点，
- 两端节点都在查询结果里的每条连线。

查询范围是当前 `Viewport` 向外扩一层图（`expansionDepth: 1`），所以刚好在视口外、但连线要穿进视口的节点仍会被包含。结果不是「节点视图列表」；连线也是条目。

## 什么会移动视口

这里不涉及 `WorkflowInput`。表面行为测量 `ScrollViewer`，调用 `SurfaceMetricsPush.PushViewport`，写入 `tree.GetHelper().Viewport` 并持久化 `tree.Layout.ViewportOffset`。赋一个新的 `Viewport` 会在调用线程上同步执行 `Virtualize`。

```csharp
tree.GetHelper().Viewport = new Viewport(localX, localY, viewportWidth, viewportHeight);
```

节点几何变化**不会**把可见集标脏。拖动节点会重绘它的卡片，但可见集要等下一次滚动、缩放或显式 `MarkDirty()`。拖动期间每帧重跑查询的开销高于「可见集晚一拍」。

## 标脏

`MarkDirty()` 请求在 tick 通道上跑一趟。这一趟会合并：下一次 tick 之前的多次调用只花一次 `Virtualize` 加一次 `BroadcastVisibleItemLayout`，后者对可见节点重发 `Anchor` 与 `Size`，让绑定的视图刷新。

```csharp
tree.GetHelper().MarkDirty();
```

## 线程规则

`VisibleItems` 绑在 UI 上，池会同步从中移除。tick 线程不能碰它。Helper 在安装时捕获 `SynchronizationContext.Current`，并把这一趟投回该上下文；在非 UI 线程安装的 Helper 必须显式给上下文：

```csharp
var helper = new TreeHelper(200).WithSynchronizationContext(uiContext);
```

传 `null` 是显式的「在 tick 线程原地执行」，对服务、控制台宿主或无头测试是正确选择。每次 `Install` 都会重新捕获上下文，除非它被显式设过；所以把 Helper 移到另一个 UI 线程会自然改绑。

## 查询之前索引必须补齐

`SpatialGridHashMap.Query` 先跑 `EnsureIndexed()`：补上被延后的那次 resync，并给登记时边界为空的条目重读一次 `Bounds`。登记之后才被测量的条目因此会被下一次查询找到。省掉这一步，这类条目会永久不可见——移动视口也救不回来。

## 预期结果

- 八个节点铺在比视口大的世界里时，`Helper.VisibleItems.Count` 小于 `tree.Nodes.Count`。
- 滚动会把新节点带进集合，把离开的移除。
- 刚好拖出视口的节点会保留卡片到下一次滚动；之后被移除。
- 用无参 `TreeHelper` 时，`VisibleItems.Count` 保持 0，所有节点都必须直接绑定。

## 下一页

[托管视图](../02_托管视图/index.md)把这个可见集变成视图。
