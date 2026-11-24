# 小地图数学

适配、局部映射、视口矩形与拖动转换都是 `WorkflowSurfaceMath` 上的静态函数。它们由每家适配器的渲染器与管线共用，因此自定义覆盖层算出的几何与默认覆盖层一致。

这些函数返回的矩形类型 `WorkflowBounds` 在[表面数学](../../07_画布输入与导航/03_表面数学/index.md)中说明。

## WorkflowSurfaceMath（小地图成员）

```csharp
public static class WorkflowSurfaceMath
```

### 适配

| 签名 | 返回 | 说明 |
|---|---|---|
| `MinimapFit(double contentWidth, double contentHeight, double drawWidth, double drawHeight, double padding)` | `(double OriginX, double OriginY, double Scale)` | 计算把内容装进带内边距绘制区域的统一比例，以及让内容居中的原点。 |

### 内容到小地图

| 签名 | 返回 | 说明 |
|---|---|---|
| `MinimapLocal(double contentX, double contentY, double contentLeft, double contentTop, double originX, double originY, double scale)` | `(double LocalX, double LocalY)` | 把画布局部点映射到小地图局部像素。 |
| `MinThumbSize(double size, double scale, double min)` | `double` | 把缩放后的缩略块边长抬到至少 `min`。 |
| `MinimapViewportRect(double originX, double originY, double scale, double vpLeft, double vpTop, double vpWidth, double vpHeight, double contentLeft, double contentTop, double mmWidth, double mmHeight, double minRectSize)` | `(double X, double Y, double Width, double Height)` | 把视口映射进小地图并把指示块钳制在框内；最小边长为 `minRectSize`。 |

### 小地图到滚动

| 签名 | 返回 | 说明 |
|---|---|---|
| `MinimapToCanvasLocal(double mmX, double mmY, double originX, double originY, double scale, double contentLeft, double contentTop)` | `(double LocalX, double LocalY)` | `MinimapLocal` 的逆变换。 |
| `MinimapToScroll(double localX, double localY, double viewportWidth, double viewportHeight, double contentOffsetX, double contentOffsetY)` | `(double ScrollX, double ScrollY)` | 把画布局部点转换成让它居中的滚动偏移。 |

## 管线用法

| 步骤 | 函数 |
|---|---|
| 适配映射内容 | `MinimapFit`，绘制区域先减去 `Metrics.Padding`。 |
| 节点矩形 | `MinimapLocal`，再用 `Metrics.MinimumThumbSize` 调 `MinThumbSize`。 |
| 视口指示块 | `MinimapViewportRect`，最小边长 2 px。 |
| 拖动 | `MinimapToCanvasLocal`，再 `MinimapToScroll`，然后管线的滚动钳制与 `IMinimapViewportHost.ApplyScroll`。 |

## 说明

- 比例是统一的；非方形绘制区域留下边距，而不是拉伸地图。
- `MinimapViewportRect` 把指示块钳制在框内，因此比内容还大的视口仍能显示有意义的矩形。
- `MinThumbSize` 防止远处节点消失；它影响绘制，不影响命中测试。
