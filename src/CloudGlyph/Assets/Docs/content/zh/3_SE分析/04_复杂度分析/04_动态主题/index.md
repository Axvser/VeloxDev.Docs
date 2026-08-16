# 复杂度分析 — 动态主题

设 $N$ = 已注册主题感知对象数，$P$ = 每个对象的主题属性数，$S$ = 一次过渡的插值帧数，$T$ = 已注册类型数，$K$ = 主题数。

## 核心操作

### 主题值查找（`ThemeCache`）

$$O(P) \quad \text{每个类型（属性扫描）}, \quad O(1) \quad \text{每个属性查找}$$

- 静态默认值存储于 `Dictionary<Type, Dictionary<string, PropertyEntry>>`；`TryGetDefaultValue` 沿继承链（`type.BaseType`）查找，因此对于浅层级结构，查找为 $O(\text{深度}) \approx O(1)$。
- `GetStaticForType` 每次调用都会沿继承链收集条目并重建合并字典 —— 最坏情况每次调用 $O(P \cdot \text{深度})$。

### 按实例活跃缓存（`GetOrCreateActiveEntry`）

$$O(1) \quad \text{摊还}$$

- 由 `ConditionalWeakTable<IThemeObject, InstanceCache>.GetValue` 支持，这是基于哈希的查找 —— 摊还 $O(1)$。条目每个实例只创建一次，并随实例一起被回收。

### 注册 / 注销（`ThemeManager`）

$$O(1) \quad \text{每次调用}$$

- `Register` 先做一次 `ConditionalWeakTable.TryGetValue`（防重复），然后向列表添加一个 `WeakReference<IThemeObject>`。`Unregister` 移除缓存条目，并通过 `RemoveAll` 移除匹配的弱引用 —— `RemoveAll` 最坏情况 $O(N)$，典型调用摊还 $O(1)$。
- `InitializeTheme()` 还会在 `ThemeCache` 中一次性注册类型（摊还 $O(P)$），并向实例应用当前主题（$O(P)$）。

### 带动画切换（`Transition<T>`）

$$O(N \cdot P \cdot S)$$

对于 $N$ 个对象中的每个、其 $P$ 个属性中的每个，`CalculateFrames` 产生 $S$ 帧：

$$S = \max\left(1,\; \left\lfloor \frac{\text{Duration} \times FPS}{1000} \right\rfloor\right)$$

- 每属性帧预计算：$O(S)$（每帧一次插值 + 一次缓动求值）。
- 帧应用：$S$ 步顺序 `Task.Delay(deltaTime)`，每步调用一个入队的动作，对每个属性执行一次 `PropertyInfo.SetValue` —— **墙钟时间** $O(S \cdot \Delta t)$，即受 `Duration` 约束。
- 预计算帧队列与每属性帧数组的临时内存：$O(N \cdot P \cdot S)$。

以 `TransitionEffects.Theme`（$FPS = 60$，$Duration = 0.46s$）为例：

$$S = \left\lfloor \frac{460 \times 60}{1000} \right\rfloor = 27 \quad \text{每属性帧数}$$

### 即时切换（`Jump<T>`）

$$O(N \cdot P)$$

无插值；`steps = 1`、`deltaTime = 0`。每个属性直接设置为目标值。

### 运行时覆盖（`SetThemeValue<T>`）

$$O(P)$$

在实例的活跃缓存（`InstanceCache.Overrides`）中写入一条覆盖记录，并将属性更新为当前主题。

## 内存占用

| 结构 | 复杂度 | 说明 |
|---|---|---|
| 静态主题缓存（每个已注册类型） | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`，以声明类型为键；每个属性每个主题保存一个值。 |
| 活跃实例覆盖 | $O(N \cdot P)$ | `ConditionalWeakTable<IThemeObject, InstanceCache>` — 弱键，无泄漏。 |
| `ThemeManager` 活跃实例列表 | $O(N)$ | `List<WeakReference<IThemeObject>>`；每次过渡时清理失效条目（$O(N)$）。 |
| 过渡帧缓冲 | $O(N \cdot P \cdot S)$ | 过渡期间临时；`ExecuteTransition` 完成后释放。 |
| 转换器注册表 | $O(C)$ | `Dictionary<string, IThemeValueConverter>`，$C$ = 已注册转换器数。 |

## 支撑结构的查找成本

| 操作 | 复杂度 |
|---|---|
| 插值器注册表查找（`InterpolatorCore.NativeInterpolators`） | $O(1)$ — `ConcurrentDictionary<Type, IValueInterpolator>` |
| 按键查找转换器（`ThemeCache.GetConverter`） | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` 起始值读取 | $O(1)$ — 先活跃缓存，再静态字典 |
| `StartModel.Reflect` 起始值读取 | 每个属性 $O(1)$（`PropertyInfo.GetValue`）—— 每个对象每次过渡 $O(P)$ |

## 说明

- `StartModel.Cache` 在动画开始时避免反射；`StartModel.Reflect` 通过 `PropertyInfo.GetValue` 读取实时属性值 —— 每属性开销可忽略，但每个对象每次过渡为 $O(P)$。
- 弱引用设计意味着：一个注册的对象若在其它地方不可达，就会被回收（并在下一次过渡时被清理），因此长期运行的编辑器不会累积主题注册。

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（第 83–106 行 `Transition`、第 121–143 行 `Jump`、第 153–407 行 `CalculateFrames`、第 414–452 行 `ExecuteTransition`）、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`。
