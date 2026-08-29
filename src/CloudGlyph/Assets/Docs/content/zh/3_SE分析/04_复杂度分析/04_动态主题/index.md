# 复杂度分析 — 动态主题

设 $N$ = 已注册主题感知对象数，$P$ = 每个对象的主题属性数，$T$ = 已注册类型数，$K$ = 主题数。（采样是连续的/Stopwatch 驱动，因此没有预计算的帧数 $S$。）

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

$$O(N \cdot P) \text{ 准备} \quad + \quad \text{每次采样 } O(N \cdot P)$$

对于 $N$ 个对象中的每个、其 $P$ 个属性中的每个，`PrepareSamplers` 解析一个 `ISampleable`（`InterpolatorCore.TryGetInterpolator` → 值本身是 `ISampleable` → null）并 `Normalize` 得 `ISampler`，捕获 current/target 值 —— 每个属性 $O(1)$，**不构建帧列表**。`ExecuteTransition` 随后运行 Stopwatch 驱动的采样循环：

- 每次采样工作：$O(N \cdot P)$ —— 每个属性一次 `ISampler.Update`（或持有当前值）。
- 采样次数**不是**由 `FPS` 决定：它是 `elapsed / duration`，由以 `1000 / FPS` ms 为上限的粗糙 yield 间隔节流（让出，非计时依据），因此一趟每秒最多发出约 `FPS` 次采样 —— **墙钟时间**受 `Duration` 约束。`FPS` 是最大采样率上限。
- 已准备条目的临时内存：$O(N \cdot P)$（每条持有 target / property / sampler / current / targetValue）。

### 即时切换（`Jump<T>`）

$$O(N \cdot P)$$

除端点外不做采样；`ExecuteTransition` 以 `durationMs = 0` 运行，因此首次采样即 `rawT = 1`，每个属性直接设置为目标值。

### 运行时覆盖（`SetThemeValue<T>`）

$$O(P)$$

在实例的活跃缓存（`InstanceCache.Overrides`）中写入一条覆盖记录，并将属性更新为当前主题。

## 内存占用

| 结构 | 复杂度 | 说明 |
|---|---|---|
| 静态主题缓存（每个已注册类型） | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`，以声明类型为键；每个属性每个主题保存一个值。 |
| 活跃实例覆盖 | $O(N \cdot P)$ | `ConditionalWeakTable<IThemeObject, InstanceCache>` — 弱键，无泄漏。 |
| `ThemeManager` 活跃实例列表 | $O(N)$ | `List<WeakReference<IThemeObject>>`；每次过渡时清理失效条目（$O(N)$）。 |
| 已准备的采样器条目 | $O(N \cdot P)$ | 过渡期间临时；`ExecuteTransition` 完成后释放。 |
| 转换器注册表 | $O(C)$ | `Dictionary<string, IThemeValueConverter>`，$C$ = 已注册转换器数。 |

## 支撑结构的查找成本

| 操作 | 复杂度 |
|---|---|
| 采样器注册表查找（`InterpolatorCore.NativeInterpolators`） | $O(1)$ — `ConcurrentDictionary<Type, ISampleable>` |
| 按键查找转换器（`ThemeCache.GetConverter`） | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` 起始值读取 | $O(1)$ — 先活跃缓存，再静态字典 |
| `StartModel.Reflect` 起始值读取 | 每个属性 $O(1)$（`PropertyInfo.GetValue`）—— 每个对象每次过渡 $O(P)$ |

## 说明

- `StartModel.Cache` 在动画开始时避免反射；`StartModel.Reflect` 通过 `PropertyInfo.GetValue` 读取实时属性值 —— 每属性开销可忽略，但每个对象每次过渡为 $O(P)$。
- 弱引用设计意味着：一个注册的对象若在其它地方不可达，就会被回收（并在下一次过渡时被清理），因此长期运行的编辑器不会累积主题注册。

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（`Transition`、`Jump`、`PrepareSamplers`、`ExecuteTransition`）、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`。
