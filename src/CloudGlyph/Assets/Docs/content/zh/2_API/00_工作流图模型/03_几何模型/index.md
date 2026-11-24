# 几何模型

几何值类型大多是可变视图模型（`Viewport` 与 `WorkflowBounds` 是只读结构）。`Anchor` 与 `Size` 存储**世界**值；getter 返回按 `CanvasLayout.Scale` 坍缩后的视图值。

命名空间：`VeloxDev.WorkflowSystem`（程序集 `VeloxDev.Core`）。

## Anchor

**签名：** `sealed partial class Anchor(double left = 0d, double top = 0d, int layer = 0) : ICloneable, IEquatable<Anchor>`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Horizontal` | `double` | 左坐标。 |
| `Vertical` | `double` | 上坐标。 |
| `Layer` | `int` | 绘制层；由适配器解释。 |
| `Collapse(Scale?)` | `Anchor` | 朝世界原点坍缩的视图值（`value / scale`）；null 或 1 时返回自身。 |
| `Expand(Scale?)` | `Anchor` | 由视图值还原世界值（`view * scale`）；`Collapse` 的逆。 |
| `Clone()` / `Equals(...)` / `GetHashCode()` / `ToString()` | | 值语义；`ToString` 为 `Anchor(x,y,layer)`。 |
| `operator +`、`operator -` | `Anchor` | 逐分量，含 `Layer`。 |
| `operator ==`、`operator !=` | `bool` | 值相等。 |

坍缩实例在内部记住其缩放与所有者，以便序列化写出世界坐标；不要修改节点 `Anchor` getter 返回的对象——通过属性赋值。

## Size

**签名：** `sealed partial class Size(double width = 0d, double height = 0d) : ICloneable, IEquatable<Size>`

成员：`Width`、`Height`；`Collapse(Scale?)`、`Expand(Scale?)`；`Clone()`、`Equals`、`GetHashCode`、`ToString`（`Size(w,h)`）；`+`、`-`、`==`、`!=`。

## Offset

**签名：** `sealed partial class Offset(double left = 0d, double top = 0d) : ICloneable, IEquatable<Offset>`

成员：`Horizontal`、`Vertical`；`Clone()`、`Equals`、`GetHashCode`、`ToString`（`Offset(x,y)`）；`+`、`-`、`==`、`!=`。`Offset` 是增量：节点移动命令按视图空间解释它。

## Scale

**签名：** `sealed partial class Scale(double horizontal = 1d, double vertical = 1d) : ICloneable, IEquatable<Scale>`

成员：`Horizontal`、`Vertical`；`Clone()`、`Equals`、`GetHashCode`、`ToString`（`Scale(x,y)`）；`+`、`-`、`==`、`!=`。`1.0` 表示不缩放。

## ZoomCenter

**签名：** `enum ZoomCenter`

| 值 | 说明 |
| --- | --- |
| `WorldOrigin = 0` | 朝世界原点坍缩；远离 `(0,0)` 的视口可能丢失可见节点。 |
| `ViewportCenter = 1` | 围绕视口中心对应的世界点坍缩；可见内容保持原位。 |

两种模式画布几何相同；`ViewportCenter` 通过滚动把坍缩轴的世界点压在视口中心下，而不移动画布。

## CanvasLayout

**签名：** `sealed partial class CanvasLayout : ICloneable, IEquatable<CanvasLayout>`

| 成员 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `OriginSize` | `Size` | `1920×1080` | 基础画布范围。 |
| `PositiveOffset` | `Offset` | `0,0` | 正方向额外范围。 |
| `NegativeOffset` | `Offset` | `0,0` | 负方向额外范围。 |
| `Scale` | `Scale` | `1,1` | 应用到每个节点视图的缩放。 |
| `ActualSize` | `Size` | 计算值 | 可滚动范围；放大（`Scale < 1`）时按 `1/Scale` 扩展。 |
| `ActualOffset` | `Offset` | 计算值 | 等于 `NegativeOffset`。 |
| `ViewportOffset` | `Offset` | `0,0` | 当前滚动位置。 |
| `ZoomCenter` | `ZoomCenter` | `ViewportCenter` | 坍缩模式。 |
| `CollapsePivot` | `Anchor` | `0,0,0` | 适配器在缩放变化前紧邻写入的轴点。 |
| `UpdateCommand` | `IVeloxCommand` | — | 重算 `ActualSize`/`ActualOffset`；无参数。 |

方法：`AdaptTo(Size targetOriginSize, out double suggestedViewportX, out double suggestedViewportY)` 返回适配新原始尺寸的副本并计算居中视口位置；`AdaptTo(Size)` 是同一操作但不输出视口值。`Clone()`、`Equals(CanvasLayout?)`、`GetHashCode()` 覆盖几何与缩放设置。

改变 `OriginSize`、`PositiveOffset`、`NegativeOffset` 或 `Scale` 会重算 `ActualSize`/`ActualOffset` 并重新触发 `ActualSize`。只改 `CollapsePivot` 或 `ZoomCenter` 不重算画布尺寸。

## Viewport

**签名：** `readonly struct Viewport(double left, double top, double width, double height) : IEquatable<Viewport>, ISampleable`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Empty` | `Viewport` | 零尺寸视口（`default`）。 |
| `Horizontal` / `Vertical` | `double` | 左 / 上边缘。 |
| `Width` / `Height` | `double` | 尺寸。 |
| `Right` / `Bottom` | `double` | 远端边缘。 |
| `IsEmpty` | `bool` | 宽或高为零及以下时为真。 |
| `IntersectsWith(double left, double top, double width, double height)` | `bool` | 与矩形相交。 |
| `IntersectsWith(Viewport)` | `bool` | 与视口相交。 |
| `Contains(double x, double y)` / `Contains(Viewport)` | `bool` | 点或整体包含。 |
| `Union(Viewport a, Viewport b)` | `Viewport` | 最小覆盖视口。 |
| `GetAnimatableMembers()` / `CreateFrameValue(...)` | `ISampleable` | 动画支持：成员为 left、top、width、height。 |

## WorkflowBounds

**签名：** `readonly struct WorkflowBounds`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Left` / `Top` / `Width` / `Height` | `double` | init-only 边缘与尺寸。 |
| `Right` / `Bottom` | `double` | 远端边缘。 |
| `IsEmpty` | `bool` | 无面积。 |
| `FromNode(double x, double y, double w, double h)` | `WorkflowBounds` | 单节点矩形。 |
| `FromNodes(IEnumerable<(double X, double Y, double W, double H)>)` | `WorkflowBounds` | 矩形并集。 |
| `Union(WorkflowBounds a, WorkflowBounds b)` | `WorkflowBounds` | 最小覆盖范围。 |

`WorkflowBounds` 也是布局成本度量回报的范围类型；见[布局解](../../06_工作流自动布局/02_布局解/index.md)。

## 示例

```csharp
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 2), Size = new Size(220, 120) };
var tree = new TreeDefaultViewModel();
tree.GetHelper().CreateNode(node);

tree.Layout.Scale = new Scale(0.5, 0.5);
Console.WriteLine(node.Anchor);            // Anchor(120,160,2)：坍缩后的视图值
Console.WriteLine(node.GetWorldAnchor());  // Anchor(60,80,2)：存储的世界值
Console.WriteLine(tree.Layout.ActualSize); // Scale 0.5 时为 3840x2160
```
