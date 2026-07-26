# 过渡动画系统 — API 参考

## 命名空间：`VeloxDev.TransitionSystem`

### 核心抽象（`VeloxDev.TransitionSystem.Abstractions`）

#### `TransitionCore<TTarget, TStateSnapshotCore>`
类型安全过渡操作的基类。

| 方法 | 描述 |
|---|---|
| `Create()` | 为目标类型创建新的状态快照 |
| `Execute(TTarget, StateSnapshotCore)` | 在目标上执行状态快照 |
| `Execute(StateSnapshotCore)` | 执行状态快照（目标已设置） |
| `Execute(TTarget, IEnumerable<StateSnapshotCore>)` | 在目标上执行多个快照 |
| `Exit(TTarget)` | 退出目标上的所有活动过渡 |

#### `TransitionCore`
非泛型基类，提供静态 `Exit()` 用于生命周期管理。

#### `StateSnapshotCore<TTarget>`
捕获并应用目标对象上的属性值变更。

| 方法 | 描述 |
|---|---|
| `Property<T>(Expression<Func<TTarget, T>>)` | 选择要动画的属性，返回属性构建器 |
| `AsRoot()` | 将此快照标记为根（独立执行） |
| `CoreExecute(TTarget, bool)` | 在目标上执行快照 |

#### `TransitionProperty`
表示用于深层属性导航的属性访问器链。

| 属性 | 类型 | 描述 |
|---|---|---|
| `Path` | `string` | 点分隔的属性路径（例如 "Background.Color"） |
| `PropertyType` | `Type` | 叶子属性的类型 |
| `CanRead` | `bool` | 所有段是否支持读取 |
| `CanWrite` | `bool` | 叶子属性是否支持写入 |

| 方法 | 描述 |
|---|---|
| `GetValue(object)` | 通过属性链读取当前值 |
| `SetValue(object, object?)` | 通过属性链写入值 |

#### `TransitionSchedulerCore`
管理多个过渡的时间和生命周期。

| 方法 | 描述 |
|---|---|
| `Add(StateSnapshotCore, object)` | 调度快照执行 |
| `Remove(StateSnapshotCore)` | 移除待处理的快照 |
| `Start()` | 启动（或恢复）处理 |
| `Pause()` | 暂停所有活动过渡 |
| `Exit()` | 停止并清理所有过渡 |

### 枚举

| 枚举 | 值 |
|---|---|
| `RotationDirection` | `Shortest`, `Longest`, `CW`, `CCW` |
| `State` | 过渡状态标志 |

### 接口（`VeloxDev.TransitionSystem`）

| 接口 | 用途 |
|---|---|
| `IEaseCalculator` | 定义缓动曲线（`Ease(double t) → double`） |
| `IValueInterpolator` | 在起始值和结束值之间生成中间值 |
| `ITransitionScheduler` | 调度器生命周期契约 |
| `ITransitionProperty` | 属性访问抽象 |
| `ITransitionInterpreter` | 解释过渡配置 |
| `ITransitionEffect` | 可视化过渡效果 |
| `IFrameInterpolator` | 帧级别插值 |
| `IFrameSequence` | 插值帧序列 |
| `IFrameState` | 特定帧的状态 |
| `IInterpolable` | 使类型可插值 |
| `IUIThreadInspector` | UI 线程感知 |

### 缓动函数工厂（`VeloxDev.TransitionSystem.Eases`）

| 类别 | In | Out | InOut |
|---|---|---|---|
| `Sine` | `Eases.Sine.In` | `.Out` | `.InOut` |
| `Quad` | `Eases.Quad.In` | `.Out` | `.InOut` |
| `Cubic` | `Eases.Cubic.In` | `.Out` | `.InOut` |
| `Quart` | `Eases.Quart.In` | `.Out` | `.InOut` |
| `Quint` | `Eases.Quint.In` | `.Out` | `.InOut` |
| `Expo` | `Eases.Expo.In` | `.Out` | `.InOut` |
| `Circ` | `Eases.Circ.In` | `.Out` | `.InOut` |
| `Back` | `Eases.Back.In` | `.Out` | `.InOut` |
| `Elastic` | `Eases.Elastic.In` | `.Out` | `.InOut` |
| `Bounce` | `Eases.Bounce.In` | `.Out` | `.InOut` |

### 插值器注册表（`InterpolatorCore`）

| 方法 | 描述 |
|---|---|
| `RegisterInterpolator(Type, IValueInterpolator)` | 为类型注册插值器 |
| `TryGetInterpolator(Type, out IValueInterpolator?)` | 获取已注册的插值器 |
| `UnregisterInterpolator(Type, out IValueInterpolator?)` | 移除注册 |
| `NativeInterpolators` | 内置插值器字典 |

### TransitionEffect（`TransitionEffect`, `TransitionEx`）

提供更高级的过渡编排：

| 方法 | 描述 |
|---|---|
| `TransitionEffect.Create<T>()` | 创建过渡效果 |
| `TransitionEx.Animate<T>(T target, Action<T> to, ...)` | 流畅动画 API |
