# 复杂度分析 — 动态主题

设 $N$ = 已注册主题感知对象数，$P$ = 每个对象的主题属性数，$T$ = 已注册类型数，$K$ = 主题数，$C$ = 已注册转换器数。带动画的切换如今由平台的 `TransitionSchedulerCore` 执行，因此帧数与帧节拍归效果（`FPS`）所有，墙钟耗时由效果的 `Duration` 界定而非由元素数决定：一场切换的所有目标锚定在同一条 `TransitionTimeline` 上。

## 核心操作

### 静态注册与查找（`ThemeCache`）

$$
O(P) \ \text{每类型注册}, \quad O(\text{深度}) \approx O(1) \ \text{每次默认值查找}
$$

- 默认值存于 `Dictionary<Type, Dictionary<string, PropertyEntry>>`，其中 `PropertyEntry` 将一个 `PropertyInfo` 与一个主题值 `Dictionary<Type, object?>` 配对。`RegisterType` 每类型复制 $P$ 条并以 `IsTypeRegistered`（$O(1)$）守卫 —— 重复被忽略。
- `TryGetDefaultValue` 沿 `type.BaseType` 走到 `object`，每层做哈希查找：$O(\text{深度})$。
- `GetStaticForType`（由生成的 `GetStaticThemeCache` 调用）每次调用都沿继承链收集并重建合并字典：每次 $O(P \cdot \text{深度})$。

### 按实例活跃缓存（`ThemeCache`）

$$
O(1) \ \text{每次查找/覆盖摊还}
$$

由 `ConditionalWeakTable<IThemeObject, InstanceCache>.GetValue`（基于哈希，摊还 $O(1)$）支撑。`PrepareSamplers` 会对每个已注册对象调用生成的 `GetActiveThemeCache()`，因此首次切换时 $N$ 个对象各创建一个空 `InstanceCache`；条目是弱键的，随实例一起被回收。

### 注册 / 注销（`ThemeManager`）

$$
O(1) \ \text{每次调用} \quad (O(N) \ \text{最坏 RemoveAll})
$$

`Register` 先以 `_act_cache.TryGetValue` 守卫，再向列表追加一个 `WeakReference<IThemeObject>` —— $O(1)$。`Unregister` 移除缓存条目并以 `RemoveAll` 扫描列表 —— 最坏 $O(N)$，典型 $O(1)$。`InitializeTheme` 附带一次性类型注册（摊还 $O(P)$）并向实例应用当前主题（$O(P)$ 反射写入）。

### 切换准备（`PrepareSamplers`）

$$
O(N \cdot P \cdot \text{深度}) \ \text{最坏}, \quad O(N \cdot P) \ \text{浅层级下}
$$

对 $N$ 个对象中的每个及其 $P$ 个属性中的每个：起始/目标值从活跃缓存再退到静态字典解析（各 $O(1)$ 哈希查找），并把该属性的 `PropertyInfo` 包装成一条 `TransitionProperty` 路径。为每个对象重建合并静态缓存为 $O(P \cdot \text{深度})$。这一层不解析采样器、也不归一化端点 —— 唯一一次触碰注册表是每个属性一次 `InterpolatorCore.TryGetInterpolator(propertyType, out _)` 探测。该探测优先精确匹配（$O(1)$），否则先沿基类链向外走、再走按名称排序的接口，因此未命中时是 $O(\text{深度} + \text{接口数})$。

`TransitionProperty.FromProperty` 由静态 `ConcurrentDictionary<PropertyInfo, TransitionProperty>` 记忆化，因此路径构造 —— 以及它在首次使用时触发的表达式编译 —— 每个不同的 `PropertyInfo` 只付一次，而不是每场切换付一次：之后摊还 $O(1)$。分组与条目的临时内存为 $O(N \cdot P)$。

### schedule 解析

$$
O(N)
$$

每个目标组一次 `InterpolatorCore.CreateScheduler(target, effect)` 调用，且**在调度任何东西之前**完成，因此整场切换得到同一个答案。首个失败 —— 没有平台插值器、组列表为空、或某个 scheduler 为 null —— 会让整场切换短路为立即落值，这也是带动画路径绝不会只覆盖一部分目标的原因。

### 带动画切换（`Transition<T>`）

$$
O(N \cdot P) \ \text{准备} \ + \ O\!\left(\frac{\text{Duration}}{\text{FPS}^{-1}}\right) \ \text{帧} \ \times \ O(P) \ \text{每目标每帧}
$$

调用的同步部分就是准备：若它真的动画起来，`Transition<T>` 的第一个 await 是各目标执行任务上的 `Task.WhenAll`，因此在它之前的一切 —— 清理、快照、`PrepareSamplers`、`WriteStartValues`、`Track`、构建 `StateCore`、调度 —— 都同步完成。随后每个目标的 scheduler 针对**共享**时间轴跑自己的采样循环，节拍由效果的 `FPS` 决定，缓动由 `effect.Ease` 决定。每目标每帧，每个有采样器的属性跑一次 `ISampler.InsertFrame`；没有采样器的属性被循环整个跳过，只在收尾时写一次。

由于时间轴是共享的，一个目标和一千个目标看到的帧数相同，切换的墙钟耗时就是效果自身的时长、与 $N$ 无关 —— 这正是规模 Demo 的 `bench` 模式所测量的性质（`Examples/Theme/WPF/Demo/BenchRunner.cs`）。

顶替一场切换是 $O(1)$ 加取消回调：`CancelActiveSwitch` 把 run 列表换出，并对每个 run 取消令牌、唤醒时间轴。

### 终值补写与落地（`RunSwitch` 收尾）

$$
O(N \cdot P)
$$

`Task.WhenAll` 之后，各目标的 run 被 untrack，`ApplyHeldValues` 为每个没有采样器的条目写入终值 —— 一趟对 $O(N \cdot P)$ 条目的遍历。`Current` 只在此处推进，且只在没有任何 run 被取消、也没有故障时推进。

### 即时切换（`Jump<T>`）

$$
O(N \cdot P)
$$

`Jump` 复用 `PrepareSamplers`，随后调用 `ApplyImmediately`：对每个终值非 null 的条目执行一次 `TransitionProperty.SetValue`，然后推进 `Current`。它不建时间轴、不解析 scheduler、不查询采样器，内部也完全没有 await 点 —— 因此它完全同步，且进行中的 `Jump` 无法被取消（尽管 `Jump` 自己会先取消进行中的带动画切换）。

### 运行时覆盖（`SetThemeValue<T>` / `RestoreThemeValue<T>`）

$$
O(1) \ \text{每属性摊还}
$$

生成的调用向实例的 `Overrides` 字典写入（或移除）一条覆盖记录，再经 `UpdatePropertyToCurrentTheme` 刷新该单个属性 —— 字典查找外加至多一次 `TryGetDefaultValue` 的继承链遍历（$O(\text{深度})$）。

## 内存占用

| 结构 | 复杂度 | 说明 |
|---|---|---|
| 静态主题缓存 | $O(T \cdot P \cdot K)$ | `ThemeCache._staticCache`，以声明类型为键；每属性每主题一个值引用外加 `PropertyInfo` 元数据。 |
| 活跃实例覆盖 | 最坏 $O(N \cdot P)$ | `ConditionalWeakTable<IThemeObject, InstanceCache>` —— 弱键、无泄漏；即使为空也会在首次切换时惰性创建。 |
| `ThemeManager` 成员登记 | $O(N)$ | `_act_cache`（`ConditionalWeakTable`，每对象空字典）+ `activeThemes`（`List<WeakReference<IThemeObject>>`）；每场切换清理失效项。 |
| 在途切换 | $O(N)$ | `_activeSwitch` 按目标各持一个 `SwitchTarget`（scheduler + run + 帧状态）；在 `Task.WhenAll` 外侧的 `finally` 中清空。 |
| 已准备的分组与条目 | $O(N \cdot P)$ | 每场切换的临时量；每属性一条 `TransitionEntry`，每目标一组 `TargetEntries`。 |
| 记忆化的属性路径 | $O(\text{不同的主题 } PropertyInfo \text{ 数})$ | `TransitionProperty.FromPropertyCache` —— 进程级且从不驱逐。上界是不同属性声明的数量，而非 $N$。 |
| 转换器注册表 | $O(C)$ | `ThemeCache._converters`；当前为空，因为生成器在注册时内联实例化转换器。 |

## 支撑结构的查找成本

| 操作 | 复杂度 |
|---|---|
| 采样器注册表查找（`InterpolatorCore.TryGetInterpolator`） | 精确匹配 $O(1)$；沿基类与接口走时 $O(\text{深度} + \text{接口数})$ |
| 属性路径工厂（`TransitionProperty.FromProperty`） | 摊还 $O(1)$ —— 静态 `ConcurrentDictionary<PropertyInfo, TransitionProperty>` |
| 按键查找转换器（`ThemeCache.GetConverter`） | $O(1)$ — `Dictionary<string, IThemeValueConverter>` |
| `StartModel.Cache` 起始值读取 | $O(1)$ — 先活跃缓存，再静态字典 |
| `StartModel.Reflect` 起始值读取 | 每属性 $O(1)$（`PropertyInfo.GetValue`）—— 每个对象每场切换 $O(P)$ |
| 控制调用的 scheduler 查找（`Transition.Pause` / `Seek` / `Exit`） | $O(1)$ — 以目标为键的 `ConditionalWeakTable` |

## 实测表现

规模 Demo 的无头 `bench` 模式（`Examples/Theme/WPF/Demo/BenchRunner.cs`，以 `dotnet run -- bench` 运行）在 1 / 50 / 200 / 1000 个已注册元素上跑同一场切换，每个规模重复 3 次，并把表格写入 `%TEMP%\veloxdev-theme-scale.tsv`。下表即该文件的数据，由 `Examples/Theme/WPF/Demo` 的 **Debug** 构建于 2026-09-13 在 .NET 9（`net9.0-windows`）、Windows 11（10.0.26200）上产出。它们衡量的是本引擎自身在不同规模下的表现 —— 不是与任何其它库的对比。1000 个元素的行还额外在方块不挂入可视化树（`attached=False`）的情况下测了一次。**绝对值在两次运行之间会变** —— 在这台机器上分配量差约三分之一、`prep_ms` 差几毫秒 —— 所以请把它们读作形状与量级，而不是精确数值。

| 元素数 | `prep_ms` | `anim_ms` | `frames` | `frames_per_target` | `alloc_kb` | `jump_ms` |
|---|---|---|---|---|---|---|
| 1 | 0.2 – 0.6 | 307.3 – 315.9 | 20 | 20 | 121 – 140 | 0.2 – 0.9 |
| 50 | 0.6 – 0.8 | 311.2 – 317.8 | 1 000 | 20 | 804 – 812 | 0.2 |
| 200 | 1.6 – 2.0 | 309.8 – 314.4 | 4 000 | 20 | 2 837 – 2 870 | 0.4 – 0.8 |
| 1000 | 7.1 – 10.0 | 310.4 – 320.4 | 18 416 – 19 833 | 18 – 20 | 12 625 – 13 533 | 1.6 – 4.5 |

- **`anim_ms` 是平的。** 每个规模都在约 310–320 ms，而声明的效果时长是 300 ms。目标数增加一千倍不带来任何额外墙钟耗时 —— 这就是「共享 `TransitionTimeline`」这条论断的实测形态，对应上文「墙钟耗时由 `Duration` 界定而非由 $N$ 界定」。
- **`prep_ms` 才是随 $N$ 增长的那部分。** 1 个元素时约 0.2–0.6 ms，1000 个时约 7–10 ms —— 线性，与上文 $O(N \cdot P)$ 的准备界吻合（每个方块 $P = 2$，外加每个目标的固定开销）。这正是 `58ae23b3` 对 `TransitionProperty.FromProperty` 的记忆化在 1000 元素规模上从约 1.6 s 降到约 10 ms 的那个量，而这些行就是记忆化之后的状态。
- **分配是按每场切换付的，不是按每帧付的。** 1000 个元素时每元素每场切换约 13–22 KB（随运行而异），而 `frames_per_target` 始终固定在 20，`gen1` / `gen2` 一路都是 0（1000 元素的行只出现一次 gen-0 回收）。分配量跟随元素数而不是帧数，说明付出代价的是准备好的条目集合，而采样循环每帧不分配。
- **`jump_ms` 即使在 1000 个元素下也只有个位数毫秒**，这与「同步、无 await 点的 `ApplyImmediately` 路径」的预期一致。

## 说明

- `StartModel` 默认为 `Cache`，避免切换开始时逐属性反射；`Reflect` 则以读取实时属性值换取这一点。无论选哪一档，准备好的起点都会在 scheduler 启动前由 `WriteStartValues` 写回目标，因为 `InterpolatorCore.Prepare` 是从目标上读取起点、而不是从条目里取。
- `TransitionProperty.FromProperty` 的记忆化正是准备阶段可扩展的原因。提交 `58ae23b3 perf(theme): memoize TransitionProperty.FromProperty` 的实测：改动前，一千个双属性元素在首帧之前约有 1.6 s 的 UI 线程停顿与 29 MB 分配；改动后约为 10 ms 与 6 MB。
- 弱引用设计意味着：一个注册对象若在别处不可达，就会被回收（并在下一次切换时被清理），因此长期运行的编辑器不会累积主题注册。规模 Demo 就依赖这一点：它丢弃一批方块后强制回收一次，使活跃集合恰好是新的一批（`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的 `Build`）。
- 逐帧写入开销很小，因为写入走编译后的 `TransitionProperty` setter，而非逐帧反射（`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`）。

> 源码引用：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`（`Transition`、`Jump`、`RunSwitch`、`PrepareSamplers`、`CancelActiveSwitch`、`ApplyImmediately`、`ApplyHeldValues`）、`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`、`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`（`CreateScheduler`、`TryGetInterpolator`）、`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`（`FromProperty`）、`Src/Generators/VeloxDev.Core.Generator/Theme.cs`。
