# 功能地图 — 过渡动画系统

## 职责

过渡动画系统提供跨平台的属性动画引擎。它处理值插值、缓动曲线、状态快照、调度和可视化过渡效果。

## 功能分解

### 1. 缓动函数（`Eases`, `IEaseCalculator`）
- **关键文件**: `TransitionSystem/Eases.cs`, `Interfaces/TransitionSystem/IEaseCalculator.cs`
- **用途**: 10 个类别共 30 个缓动函数（Sine、Quad、Cubic、Quart、Quint、Expo、Circ、Back、Elastic、Bounce），各有 In/Out/InOut 变体。

### 2. 插值器系统（`InterpolatorCore`, `IValueInterpolator`）
- **关键文件**: `TransitionSystem/Interpolator.cs`, `TransitionSystem/InterpolatorOutputCore.cs`
- **用途**: 可插拔的插值引擎。`InterpolatorCore` 维护全局类型到插值器的映射注册表。

### 3. 状态快照（`StateSnapshotCore<TTarget>`）
- **关键文件**: `TransitionSystem/State.cs`, `TransitionSystem/StateSnapshot.cs`
- **用途**: 捕获要动画的属性和它们的目标值。支持流畅配置：`.Property<T>() → .To() → .Duration() → .Ease() → .Delay()`。

### 4. 属性路径解析（`TransitionProperty`）
- **关键文件**: `TransitionSystem/TransitionProperty.cs`
- **用途**: 使用反射解析深层属性访问路径（如 `Background.Color`）。

### 5. 过渡调度器（`TransitionSchedulerCore`）
- **关键文件**: `TransitionSystem/TransitionScheduler.cs`
- **用途**: 管理执行时间线。支持 Start、Pause、Resume、Exit。

### 6. 过渡效果（`TransitionEffect`, `TransitionEx`）
- **关键文件**: `TransitionSystem/TransitionEffect.cs`, `TransitionSystem/TransitionEx.cs`
- **用途**: 多属性、多目标过渡的高级编排。

### 7. 平台适配器插值器
- **关键文件**: `Adapters/*/PlatformAdapters/Interpolators/*.cs`
- **用途**: UI 类型的平台特定插值器（Brush、Thickness、CornerRadius、Transform 等）。
