# 呈现辅助

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

这些静态辅助用普通数据、CSS 字符串与组件级订阅替代 XAML 适配器的元素属性系统。

## 类：WorkflowCanvasTransformBehavior

`public static class WorkflowCanvasTransformBehavior`

把内容平移暴露为数据和 CSS transform 字符串。

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `GetOffset(ITreeComponent tree)` | `Offset` | `tree.Layout?.ActualOffset`，或零偏移。 |
| `ToCss(Offset offset)` | `string` | `translate({H}px, {V}px)`，始终不变文化格式。 |
| `GetTransformStyle(ITreeComponent tree)` | `string` | `ToCss(GetOffset(tree))`。 |

不变文化格式很关键：逗号小数的文化会让浏览器丢掉整条声明。

## 类：WorkflowEvents

`public static class WorkflowEvents`

XAML 附着事件接收器的 Razor 对应物。在 `OnInitialized` / `OnParametersSet` 调用重载，用完释放订阅。

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Attach(INodeComponent node, INodeEventSink sink)` | `IDisposable?` | 转发节点放置与生命周期事件；helper 不提供事件时为 `null`。 |
| `Attach(ISlotComponent slot, ISlotEventSink sink)` | `IDisposable?` | 转发插槽通道事件。 |
| `Attach(ITreeComponent tree, ITreeEventSink sink)` | `IDisposable?` | 转发树连线事件。 |

### 示例：接上事件接收器

```csharp
private IDisposable? _pair;
private INodeEventSink? _sink;

protected override void OnParametersSet()
{
    _pair?.Dispose();
    _pair = Node is { } node && _sink is not null
        ? WorkflowEvents.Attach(node, _sink)
        : null;
}
// Source: source
```

被复用到另一个组件的视图必须释放旧订阅并重新附着。

## 类：WorkflowGeometryScope

`public static class WorkflowGeometryScope`

标记一次服务端缩放事务，让逐节点几何写入者让位。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `IsZooming` | `bool`（get） | 当前异步流上是否有缩放事务。 |
| `Zoom()` | `IDisposable` | 进入作用域；释放即离开。 |

### 备注

- 深度存在 `AsyncLocal<int>`，共享进程的多个电路不会看到彼此的缩放。
- 进入是计数的；嵌套或重入安全。
- 作用域期间，唯一原子互操作 `applyZoomSurface` 是几何的唯一权威。

## 类：WorkflowPresentation

`public static class WorkflowPresentation`

Blazor 树的默认调色板与输入/输出插槽辅助。

### 属性

| 名称 | 类型 | 值 |
| --- | --- | --- |
| `MinorGridColor` | `string` | `#2A2D2E` |
| `RulerBackground` | `string` | `#C8252526` 转 CSS |
| `RulerTickColor` | `string` | `#555555` |
| `RulerDividerColor` | `string` | `#3A3D40` |
| `NodeForegroundCss` | `string` | `#DD1E1E1E` 转 CSS |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `ToCss(string value)` | `string` | `#AARRGGBB` 转 `rgba(...)`；`#RRGGBB`、颜色名与 `rgb()/rgba()` 原样通过。 |
| `InputSlotsOf(INodeComponent node)` | `IEnumerable<ISlotComponent>` | 不带目标标志的纯源插槽。 |
| `OutputSlotsOf(INodeComponent node)` | `IEnumerable<ISlotComponent>` | 带目标标志的插槽。 |
| `SlotNamesOf(INodeComponent node)` | `Dictionary<ISlotComponent, string>` | 从每个枚举器的 `ConditionalSlot` 条目取名称。 |

`SlotNamesOf` 读 `IConditionalSlotProviders`；它不按名称反射节点的属性。

## 类：WorkflowRuntimeIds

`public static class WorkflowRuntimeIds`

为工作流组件分配进程生命周期内的稳定 id，供 `data-*-id` 属性使用。

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Get(object component)` | `string` | 返回 id，首次使用时分配 GUID 形式。 |
| `TryFind<T>(string? id, out T? value)` | `bool` | 从 id 解析回组件。 |
| `Enumerate()` | `IEnumerable<KeyValuePair<object, string>>` | 所有已登记 id，供诊断与测试。 |

id 存在 `ConditionalWeakTable` 中，不会让组件无法回收。

### 示例：写入运行时 id

```razor
<div data-veloxdev-node-id="@WorkflowRuntimeIds.Get(node)"></div>
```
