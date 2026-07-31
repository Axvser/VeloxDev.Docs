# 复杂度分析 — 动态主题

## 核心操作

设 $N$ = 已注册主题感知对象数，$P$ = 每个对象的主题属性数，$S$ = 一次过渡的插值帧数。

### 主题查找

$$O(1)$$

属性值存储于嵌套 `Dictionary`（`Type → PropertyName → ThemeType → value`）中，读取主题值为常数时间。

### 注册 / 注销

$$O(P) \quad \text{每个对象}$$

`InitializeTheme()` 一次性注册类型属性（摊还），随后 `ThemeManager.Register(this)` 添加一个 `WeakReference`。遍历属性以应用当前主题为 $O(P)$。

### 带动画切换（`Transition<T>`）

$$O(N \cdot P \cdot S)$$

对于 $N$ 个对象中的每个、其 $P$ 个属性中的每个，`CalculateFrames` 产生 $S$ 帧：

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

- 每属性帧计算：$O(S)$（每帧一次插值 + 一次缓动求值）。
- 帧应用：$S$ 步顺序 `Task.Delay(deltaTime)`，每步对一帧执行一次 `PropertyInfo.SetValue` —— **墙钟时间** $O(S \cdot \Delta t)$，即受 `Duration` 约束。
- 预计算帧的内存：过渡期间临时 $O(N \cdot P \cdot S)$。

以 `TransitionEffects.Theme`（$FPS = 60$，$Duration = 0.46s$）为例：

$$S = \left\lfloor \frac{460 \times 60}{1000} \right\rfloor = 27 \quad \text{每属性帧数}$$

### 即时切换（`Jump<T>`）

$$O(N \cdot P)$$

无帧；每个属性直接设置为目标值。

### 运行时覆盖（`SetThemeValue<T>`）

$$O(P)$$

在实例的活跃缓存中写入一条覆盖记录并更新属性。

## 内存占用

| 结构 | 复杂度 |
|---|---|
| 静态主题缓存（每个已注册类型） | $O(T \cdot P \cdot K)$，$T$ = 类型数，$K$ = 主题数 |
| 活跃实例覆盖 | $O(N \cdot P)$，通过 `WeakReference` 释放 — 无泄漏 |
| 过渡帧缓冲 | $O(N \cdot P \cdot S)$ 临时 |

## 说明

- `StartModel.Cache` 在动画开始时避免反射（使用缓存）；`StartModel.Reflect` 通过 `PropertyInfo.GetValue` 读取实时属性值 —— 每属性开销可忽略，但每个对象每次过渡为 $O(P)$。
- 插值器注册表查找为 $O(1)$（`ConcurrentDictionary<Type, IValueInterpolator>`）。
- 按键查找转换器为 $O(1)$（`Dictionary<string, IThemeValueConverter>`）。

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（第 83–106、153–407 行）、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`。
