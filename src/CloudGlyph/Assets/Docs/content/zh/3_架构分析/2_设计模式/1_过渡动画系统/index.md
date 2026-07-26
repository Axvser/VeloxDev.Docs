# 设计模式 — 过渡动画系统

## 1. 策略模式（缓动函数）

每个 `IEaseCalculator` 实现都是将时间 `[0, 1]` 映射到值 `[0, 1]` 的策略。`Eases` 工厂静态提供按类别组织的 30 个策略。

## 2. 注册表模式（插值器核心）

`InterpolatorCore` 实现全局类型到插值器的注册表。类型注册一次插值器；系统在过渡时动态查找。

## 3. 流畅构建器模式（状态快照配置）

`StateSnapshotCore<TTarget>.Property<T>()` 返回一个构建器，支持链式调用：
```
.Property<T>(expr).To(value).Duration(ms).Ease(ease).Delay(ms)
```

## 4. 模板方法模式（TransitionCore）

`TransitionCore<TTarget, TStateSnapshotCore>` 定义了过渡执行的骨架（创建 → 配置 → 执行 → 退出）。

## 5. 代理模式（平台适配器）

每个平台适配器提供自己的 `Interpolator`、`Transition`、`State`、`TransitionScheduler` 和 `UIThreadInspector` 实现。通过 `ThemeManager.SetPlatformInterpolator()` 注入平台特定行为。
