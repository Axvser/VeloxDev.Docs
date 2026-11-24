# 网格数学

网格装饰器画两层：内容下方的网格与内容上方的标尺。两者必须对「某个画布局部网格值落在装饰器哪个像素」达成一致。下面五个函数就是全部契约；不要为每个装饰器重新推导减法。

## WorkflowSurfaceMath（网格成员）

```csharp
public static class WorkflowSurfaceMath
```

该类与导航、小地图代码共用。这里只列网格成员；其余见[表面数学](../../07_画布输入与导航/03_表面数学/index.md)与[小地图数学](../../09_小地图/02_小地图数学/index.md)。

### 公式

| 签名 | 返回 | 公式 | 用途 |
|---|---|---|---|
| `GridCanvasLeft(double scrollOffset, double contentOffset)` | `double` | `scroll − content` | 可见画布局部区域的左边缘。 |
| `GridCanvasTop(double scrollOffset, double contentOffset)` | `double` | `scroll − content` | 可见画布局部区域的上边缘。 |
| `GridFirstLine(double localLeft, double spacing)` | `double` | `⌊localLeft / spacing⌋ · spacing` | 位于可见边缘或其下的第一条网格线。 |
| `GridX(double localValue, double localLeft, double contentRectX)` | `double` | `contentRectX + (localValue − localLeft)` | 画布局部值到装饰器内 x。 |
| `GridY(double localValue, double localTop, double contentRectY)` | `double` | `contentRectY + (localValue − localTop)` | 画布局部值到装饰器内 y。 |

在浮动带模型里，`contentRectX` 与 `contentRectY` 就是标尺厚度：网格在左侧从带之后开始，在顶部从带之下开始。

### 参数

| 参数 | 含义 |
|---|---|
| `scrollOffset` | 装饰器在该轴上被推送的滚动偏移。 |
| `contentOffset` | 该轴上被推送的画布内容偏移。 |
| `localLeft` / `localTop` | 前两个函数返回的可见画布局部边缘。 |
| `spacing` | 画布单位下的网格间距。 |
| `localValue` | 网格上的某个画布局部坐标。 |
| `contentRectX` / `contentRectY` | 内容矩形在装饰器内的原点。 |

## 绘制过程

标准绘制读取偏移、算出可见世界矩形，然后从 `GridFirstLine` 开始按 `spacing` 步进：

```csharp
var worldLeft = WorkflowSurfaceMath.GridCanvasLeft(owner.ScrollOffsetX, owner.ContentOffsetX);
var worldTop = WorkflowSurfaceMath.GridCanvasTop(owner.ScrollOffsetY, owner.ContentOffsetY);

var firstVertical = WorkflowSurfaceMath.GridFirstLine(worldLeft, spacing);
for (var value = firstVertical; value <= worldLeft + bounds.Width + spacing; value += spacing)
{
    var x = WorkflowSurfaceMath.GridX(value, worldLeft, ruler);
    // 在 x 处绘制
}
```

水平方向用 `GridCanvasTop`、`GridFirstLine` 与 `GridY` 镜像同样的步骤。

## 主线判断

`GridFirstLine` 只返回第一条对齐值；哪些线是主线由装饰器决定。比较余数时用 epsilon（0.001），不要用 `== 0`：

```csharp
var remainder = value % majorStep;
var isMajor = Math.Abs(remainder) < 0.001
    || Math.Abs(remainder - majorStep) < 0.001
    || Math.Abs(remainder + majorStep) < 0.001;
```

第一条线之后的浮点累积会让直接比较零错过之后每一条主线。

## 说明

- Core 不提供数值网格默认值；间距、主间隔与带厚度属于装饰器。WPF 模板使用 40、5、28。
- `GridFirstLine` 不做钳制；由调用方把绘制限制在可见矩形内。
- 平移改变 `scrollOffset`，从而改变可见边缘；缩放既不改变网格间距也不改变这些公式，这正是卡片缩放而网格保持像素间距的原因。
