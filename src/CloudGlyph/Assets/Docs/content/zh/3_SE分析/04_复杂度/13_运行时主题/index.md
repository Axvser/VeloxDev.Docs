# 运行时主题

一次主题切换是对已注册主题对象的扇出。管理器先清理死弱引用、快照存活的活目标、对每个调用 changing 钩子，然后要么立即写终值（`Jump`），要么每个目标跑一条过渡（`Transition`）。一切都对目标数乘属性数线性；每实例的生成成员则为每个属性增加一次基于反射的回退。

记号：已注册目标 $n$，存活目标 $T$，目标 $t$ 的主题属性 $P_t$，实际动画属性 $K_t$，声明类型成员 $m$，继承深度 $D$，已注册采样器 $R$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `Register` | 均摊 $O(1)$ | 每实例 $O(1)$ | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:75` |
| `Unregister` | $O(n)$ | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:89` |
| `SetCurrent<T>` | $O(1)$ | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:69` |
| 派发（`Transition` / `Jump`） | $O(n)$ 清理 + 快照 + 钩子 | $O(T)$ | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:112` |
| 准备采样器 | $O(\sum_t P_t D)$ | $O(\sum_t P_t)$ | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:439` |
| 动画每帧 | $O(\sum_t K_t)$ 次写入 + $O(T)$ 次派发 | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:245` |
| `Jump` 写终值 | $O(\sum_t P_t)$ 次写入 | — | `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:164` |
| `SetThemeValue` / `RestoreThemeValue` | $O(m + D)$ | $O(\text{被覆写属性})$ | `Src/Generators/VeloxDev.Core.Generator/Theme.cs:303` |
| `InitializeTheme` | $O(P) + O(D)$ 次锁 | $O(P)$ | `Src/Generators/VeloxDev.Core.Generator/Theme.cs:389` |

## 派发先清理、快照，再扇出

目标列表被扫描两次——一次丢弃死弱引用，一次构建钩子循环所用的存活数组：

```csharp
CancelActiveSwitch();
activeThemes.RemoveAll(x => !x.TryGetTarget(out _));
var actives = activeThemes.Select(x => x.TryGetTarget(out var obj) ? obj : null).Where(x => x != null).ToArray();
foreach (var themeObject in actives)
{
    themeObject?.ExecuteThemeChanging(current, themeType);
}
```

出处：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:120-126`

`Unregister` 出于同样原因是 $O(n)$：它靠扫描弱引用列表来移除。没有从实例到槽位的常数时间反查索引。

## 动画切换复用过渡引擎

切换创建一个共享时间线，然后每个目标调度一条过渡并一起等待：

```csharp
var timeline = TimerCore.CreateTimeSource<ITimeSourceControl>();
foreach (var (scheduler, group) in planned)
{
    WriteStartValues(group);
    var run = new TransitionRun(timeline);
    scheduler.Track(run);
    runs.Add(new SwitchTarget(scheduler, run, BuildState(group)));
}
Interlocked.Exchange(ref _activeSwitch, runs);
foreach (var item in runs) tasks.Add(item.Scheduler.Execute(interpolator, item.State, effect, item.Run.Cts));
await Task.WhenAll(tasks);
```

出处：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs:239-268`

起始值是反射级写入，$O(\sum_t P_t)$，发生在循环启动前。每帧代价与每条 $k = K_t$ 个属性的过渡相同，再对目标求和：

$$
T_{\text{switch}}(T) = O\!\left(\sum_t K_t\right) + O(T)\ \text{次派发}
$$

```plot
{
  "title": "主题切换代价与存活目标数",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 500] },
  "data": [
    { "fn": "10*x", "color": "#4a9eff", "title": "每目标 10 个属性" },
    { "fn": "40*x", "color": "#f472b6", "title": "每目标 40 个属性" }
  ]
}
```

`Jump` 跳过动画，同步写所有终值，顺序相同，无定时器。`SetCurrent` 只改类型字段，是常数时间。

## 每实例覆写与静态缓存

`SetThemeValue` 按需创建嵌套字典并用反射解析属性；恢复时移除覆写并更新属性。生成的更新路径回退到默认值查找，它遍历基类型，每层取一次缓存锁：

```csharp
while (current != null && current != typeof(object))
{
    lock (_lock) { if (_staticCache.TryGetValue(current, out var props) && props.TryGetValue(propertyName, out var entry) && entry.Values.TryGetValue(themeType, out value)) return true; }
    current = current.BaseType;
}
```

出处：`Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs:127-141`

这使一次覆写或回退查找为 $O(m + D)$：$m$ 用于反射成员查找，$D$ 用于继承遍历。`InitializeTheme` 付出一次类型注册，随后每实例一个全新的静态缓存字典，以及每个主题属性一次反射 set。

## 内存

静态缓存每个声明类型与属性保存一个条目，值字典按主题数大小：$O(\text{类型} \times \text{属性} \times \text{主题})$。覆写按实例存在弱表中，$O(\text{实例} \times \text{被覆写属性} \times \text{主题})$。一次切换临时分配每目标每属性一个条目，加一条共享时间线和每目标一个过渡运行；`_activeSwitch` 保留它们直到切换完成或更新的切换取消它。
