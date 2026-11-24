# 空间虚拟化

虚拟化是树 Helper 的属性。带格子尺寸构建的 Helper 会安装空间索引并维护 `VisibleItems`；无参构建的 Helper 让集合保持为空，所有内容都靠直接绑定渲染。

## TreeHelper

```csharp
public class TreeHelper : TreeHelper<ITreeComponent>
```

| 构造函数 | 行为 |
|---|---|
| `TreeHelper()` | 关闭虚拟化；`VisibleItems` 始终为空。 |
| `TreeHelper(double cellSize)` | 打开虚拟化；格子尺寸是空间网格在画布单位下的格子大小。若共享的 `TreeHelper` tick 通道未运行，则以 10 fps 启动它。 |

`TreeHelper<T>` 有相同的两个构造函数，并声明为 `partial`，由生成器补充 tick 与属性管线。

### 虚拟化成员

| 成员 | 类型 | 说明 |
|---|---|---|
| `VisibleItems` | `ObservableCollection<IWorkflowComponent>` | 可见集：虚拟连线、视口附近的节点，以及端点在查询内的连线。生成属性，带变更跟踪。 |
| `Viewport` | `Viewport` | 当前视口。赋值会调用 `Component?.Virtualize(value)`。 |
| `Component` | `T?` | 已安装的树（当它匹配 `T`）。 |
| `Input` | `InputRelay` | 树的路由输入。 |
| `NodeAdded` / `NodeRemoved` | `EventHandler<INodeComponent>` | 节点进入或离开树时触发。 |
| `LinkAdded` / `LinkRemoved` | `EventHandler<ILinkComponent>` | 连线进入或离开树时触发。 |
| `VisibleItemAdded` / `VisibleItemRemoved` | `EventHandler<IWorkflowComponent>` | 可见集变化时触发。 |

| 方法 | 说明 |
|---|---|
| `Install(ITreeComponent tree)` | 重置可见集、订阅节点/连线集合、捕获 `SynchronizationContext.Current`（除非已显式设置），并通过 `EnableMap(CellSize, VisibleItems)` 启用空间索引。 |
| `Uninstall(ITreeComponent tree)` | 取消订阅、清空索引（`ClearMap`）、清空可见集，并丢弃自动捕获的上下文。 |
| `Virtualize(Viewport viewport)` | 转发到 `Component?.Virtualize(viewport)`。 |
| `WithSynchronizationContext(SynchronizationContext? context)` | 把虚拟化批次绑定到 UI 上下文。`null` 表示在 tick 线程上就地运行。显式值在之后的安装中继续有效。返回 Helper。 |
| `MarkDirty()` | 在下一次 tick 请求一次合并的虚拟化。 |

节点几何变化不会把可见集标脏；拖动只重绘卡片，可见集等待下一次滚动、缩放或 `MarkDirty()`。

## Viewport

```csharp
public readonly struct Viewport : IEquatable<Viewport>, ISampleable
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Viewport(double left, double top, double width, double height)` | 构造函数 | 创建视口。 |
| `Empty` | `static Viewport` | 默认值。 |
| `Horizontal` / `Vertical` | `double` | 左、上边缘。 |
| `Width` / `Height` | `double` | 尺寸。 |
| `Right` / `Bottom` | `double` | `Horizontal + Width` 与 `Vertical + Height`。 |
| `IsEmpty` | `bool` | 宽或高至多为零。 |

| 方法 | 说明 |
|---|---|
| `IntersectsWith(double left, double top, double width, double height)` | 矩形相交测试。 |
| `IntersectsWith(Viewport other)` | 视口相交测试。 |
| `Contains(double x, double y)` | 点测试。 |
| `Contains(Viewport other)` | 包含测试。 |
| `Union(Viewport a, Viewport b)` | 两个视口的并集。 |
| `GetAnimatableMembers()` / `CreateFrameValue(...)` | `ISampleable` 的采样支持。 |

实现了值相等、`==`、`!=`、`GetHashCode` 与 `ToString`。

## ISpatialMap 与 ISpatialBoundsProvider

```csharp
public interface ISpatialMap<T> where T : class, ISpatialBoundsProvider
{
    Viewport Bounds { get; }
    void Insert(T item);
    void Remove(T item);
    IEnumerable<T> Query(Viewport viewport);
    void Clear();
}

public interface ISpatialBoundsProvider : INotifyPropertyChanged
{
    Viewport Bounds { get; }
}
```

几何变化时，边界提供者必须以 `"Bounds"` 为名触发 `PropertyChanged`。

## SpatialGridHashMap

```csharp
public class SpatialGridHashMap<T>(double cellSize) : ISpatialMap<T>
    where T : class, ISpatialBoundsProvider
```

格子尺寸在内部钳制到至少 1。

| 成员 | 说明 |
|---|---|
| `Bounds` | 覆盖所有已注册项的最小视口；没有项时为 `Viewport.Empty`。 |
| `Insert(T item)` | 注册项并订阅其 `PropertyChanged`。空或 NaN 边界会被跟踪，稍后索引。 |
| `Remove(T item)` | 注销并取消订阅。 |
| `Query(Viewport viewport)` | 惰性返回相交项。零尺寸项按点测试。回答前会冲刷延迟与后测量的条目。 |
| `Clear()` | 取消订阅并清空项、格子与边界。 |

## CellKey

```csharp
public readonly struct CellKey(int x, int y) : IEquatable<CellKey>
```

| 成员 | 说明 |
|---|---|
| `X` / `Y` | 列、行索引。 |
| `Equals(CellKey)` / `Equals(object?)` / `GetHashCode()` | 值相等。 |
| `ToString()` | `CellKey(X, Y)`。 |
| `==` / `!=` | 运算符。 |

## WorkflowSpatialManager

```csharp
public sealed class WorkflowSpatialManager : IDisposable
```

| 成员 | 说明 |
|---|---|
| `WorkflowSpatialManager(ITreeComponent tree, double cellSize)` | 索引已有节点与连线，并订阅 Helper 的节点/连线事件。树为 null 时抛 `ArgumentNullException`。 |
| `GlobalBounds` | 节点图与节点对图的并集。 |
| `QueryNodes(Viewport viewport)` | 惰性返回与视口相交的单独可见节点。 |
| `Dispose()` | 幂等；取消订阅、销毁提供者并清空索引。 |

管理器活在树 Helper 内部；宿主通常通过 `TreeHelper` 使用虚拟化，不会自行构造它。

## WorkflowSpatialEx

```csharp
namespace VeloxDev.WorkflowSystem.StandardEx;

public static class WorkflowSpatialEx
```

| 签名 | 返回 | 说明 |
|---|---|---|
| `EnableMap<T>(this ITreeComponent tree, double cellSize, T observable)` | `int` | 启用虚拟化并绑定可见集合。格子非正返回 `-1`，已启用返回 `0`，成功返回 `1`。 |
| `Virtualize(this ITreeComponent tree, Viewport viewport)` | `void` | 重建可见集合：虚拟连线加可见节点与连线。空视口是空操作；未启用索引时抛 `ArgumentNullException`。 |
| `ClearMap(this ITreeComponent tree)` | `int` | 把树从索引与 observable 中移除。位掩码：1 管理器已移除、2 管理器未移除、4 observable 已移除、8 observable 未移除。 |
| `SetVirtualizeInset(this ITreeComponent tree, double left = 0, double top = 0, double right = 0, double bottom = 0)` | `void` | 在不移动权威视口的前提下，向每边扩张查询。负值钳制为零。用于标尺带。 |
| `QueryNodes(this ITreeComponent tree, Viewport viewport)` | `IEnumerable<INodeComponent>` | 惰性返回相交节点；未启用索引时抛异常。 |
| `QueryNodes(this ITreeComponent tree, Anchor from, Anchor to)` | `IReadOnlyList<INodeComponent>` | 两个角之间物化的框选结果；顺序任意。 |

## WorkflowNodeScaleTracker

```csharp
public sealed class WorkflowNodeScaleTracker
```

监听父树的 `CanvasLayout.Scale`。缩放变化时调用回调并执行 `MarkDirty()`，让节点重新抛出 `Anchor` 与 `Size` 以触发再虚拟化。

| 成员 | 说明 |
|---|---|
| `Attach(ITreeComponent? tree, Action onScaleDirty)` | 挂到树上。传 `null` 即解除。重复传同一棵树只替换回调。 |
| `Detach()` | 从树与布局退订并清空回调。 |

跟踪器同时跟随被替换的 `Layout` 与被替换的树。缩放改变节点的有效尺寸、但没有给节点赋任何属性时，节点视图使用它。

## 说明

- `VisibleItems` 绑定到 UI，tick 线程不得触碰。Helper 把批次投递回捕获的上下文。
- 在 UI 线程之外安装的 Helper 必须显式给出上下文；服务或无头测试传 `null` 是正确选择。
- `SpatialGridHashMap.Query` 先调用 `EnsureIndexed`，因此注册后才测量的条目会被下一次查询找到。
