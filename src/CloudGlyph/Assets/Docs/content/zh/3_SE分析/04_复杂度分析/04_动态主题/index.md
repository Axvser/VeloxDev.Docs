# 复杂度分析 — 动态主题

设 $N$ = 已注册主题感知对象数，$P$ = 每个对象的主题属性数，$T$ = 已注册类型数，$K$ = 主题数，$C$ = 已注册转换器数。主题切换是连续的 / Stopwatch 驱动：没有预计算的帧数，帧率由粗糙的 `Task.Delay(1)` 让出界定，而不是由效果的 `FPS` 界定。

## 核心操作

### 静态注册与查找（`ThemeCache`）

$$O(P) \ \text{每类型注册}, \quad O(\text{深度}) \approx O(1) \ \text{每次默认值查找}$$

- 默认值存于 `Dictionary<Type, Dictionary<string, PropertyEntry>>`，其中 `PropertyEntry` 将一个 `PropertyInfo` 与一个主题值 `Dictionary<Type, object?>` 配对。`RegisterType` 每类型复制 $P$ 条并以 `IsTypeRegistered`（$O(1)$）守卫 —— 重复被忽略。
- `TryGetDefaultValue` 沿 `type.BaseType` 走到 `object`，每层做哈希查找：$O(\text{深度})$。
- `GetStaticForType`（由生成的 `GetStaticThemeCache` 调用）每次调用都沿继承链收集并重建合并字典：每次 $O(P \cdot \text{深度})$。

### 按实例活跃缓存（`ThemeCache`）

$$O(1) \ \text{每次查找/覆盖摊还}$$

由 `ConditionalWeakTable<IThemeObject, InstanceCache>.GetValue`（基于哈希，摊还 $O(1)$）支撑。`PrepareSamplers` 会对每个已注册对象调用生成的 `GetActiveThemeCache()`，因此首次切换时 $N$ 个对象各创建一个空 `InstanceCache`；条目是弱键的，随实例一起被回收。

### 注册 / 注销（`ThemeManager`）

$$O(1) \ \text{每次调用} \quad (O(N) \ \text{最坏 RemoveAll})$$

`Register` 先以 `_act_cache.TryGetValue` 守卫，再向列表追加一个 `WeakReference<IThemeObject>` —— $O(1)$。`Unregister` 移除缓存条目并以 `RemoveAll` 扫描列表 —— 最坏 $O(N)$，典型 $O(1)$。`InitializeTheme` 附带一次性类型注册（摊还 $O(P)$）并向实例应用当前主题（$O(P)$ 反射写入）。

### 切换准备（`PrepareSamplers`）

$$O(N \cdot P)$$

对 $N$ 个对象中的每个及其 $P$ 个属性中的每个：起始/目标值从活跃缓存再退到静态字典解析（$O(1)$ 哈希查找）；经 `InterpolatorCore.TryGetInterpolator` 解析采样器（$O(1)$，`ConcurrentDictionary`）；再由采样器 `NormalizeStart`/`NormalizeEnd` 产生端点（值采样器 $O(1)$）。为每个对象重建合并静态缓存为 $O(P \cdot \text{深度})$，浅层级下整体 $O(N \cdot P)$。已准备条目的临时内存为 $O(N \cdot P)$。

### 带动画切换（`Transition<T>`）

$$O(N \cdot P) \ \text{准备} \ +\ \text{每帧 } O(N \cdot P),\quad \text{帧数} \approx \frac{\text{Duration}}{\text{让出周期}}$$

`ExecuteTransition` 先等待静态 `SemaphoreSlim`（各趟串行，$O(1)$），再运行 Stopwatch 循环。每帧对每个属性调用一次 `ISampler.InsertFrame`（或端点写入）—— $O(N \cdot P)$ —— 并以 `await Task.Delay(1)` 让出。由于 `Task.Delay(1)` 以操作系统定时器粒度（Windows 上约 1-15 ms）解析，帧数大致等于 `Duration` 除以该周期；从不构建帧列表。新切换会经 `CancellationTokenSource` 取消正在运行的那一趟。

### 即时切换（`Jump<T>`）

$$O(N \cdot P)$$

`Jump` 复用 `PrepareSamplers` + `ExecuteTransition` 并以 `durationMs = 0` 运行，因此首帧即 `rawT = 1`，每个属性直接写为目标值 —— 单趟 $O(N \cdot P)$。

### 运行时覆盖（`SetThemeValue<T>` / `RestoreThemeValue<T>`）

$$O(1) \ \text{每属性摊还}$$

生成的调用向实例的 `Overrides` 字典写入（或移除）一条覆盖记录，再经 `UpdatePropertyToCurrentTheme` 刷新该单个属性 —— 字典查找外加至多一次 `TryGetDefaultValue` 的继承链遍历（$O(\text{深度})$）。

## 内存占用

| 结构 | 复杂度 | 说明 |
|---|---|---|
| 静态主题缓存 | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`，以声明类型为键；每属性每主题一个值引用外加 `PropertyInfo` 元数据。 |
| 活跃实例覆盖 | 最坏 $O(N \cdot P)$ | `ConditionalWeakTable<IThemeObject, InstanceCache>` —— 弱键、无泄漏；即使为空也会在首次切换时惰性创建。 |
| `ThemeManager` 成员登记 | $O(N)$ | `_act_cache`（`ConditionalWeakTable`，每对象空字典）+ `activeThemes`（`List<WeakReference<IThemeObject>>`）；每趟清理失效项。 |
| 已准备的采样器条目 | $O(N \cdot P)$ | 每次切换的临时量；`ExecuteTransition` 返回时释放。 |
| 转换器注册表 | $O(C)$ | `ThemeCache._converters`；当前为空，因为生成器在注册时内联实例化转换器。 |

## 支撑结构的查找成本

| 操作 | 复杂度 |
|---|---|
| 采样器注册表查找（`InterpolatorCore.NativeInterpolators`） | $O(1)$ — `ConcurrentDictionary<Type, ISampler>` |
| 按键查找转换器（`ThemeCache.GetConverter`） | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` 起始值读取 | $O(1)$ — 先活跃缓存，再静态字典 |
| `StartModel.Reflect` 起始值读取 | 每属性 $O(1)$（`PropertyInfo.GetValue`）—— 每个对象每趟切换 $O(P)$ |

## 说明

- `StartModel` 默认为 `Cache`，避免动画开始时逐属性反射；`Reflect` 则以读取实时属性值换取这一点。
- 弱引用设计意味着：一个注册对象若在别处不可达，就会被回收（并在下一次切换时被清理），因此长期运行的编辑器不会累积主题注册。
- 带动画的趟在每帧上的 CPU 开销很小，因为采样器写入走编译后的 `TransitionProperty` setter，而非逐帧反射（`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`，60-68、124-184 行）。

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（`Transition`、`Jump`、`PrepareSamplers`、`ExecuteTransition`）、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`、`Src/Generators/VeloxDev.Core.Generator/Theme.cs`。
