# API — 动态主题 · 平台适配器

平台适配器为一次主题切换在具体 UI 框架上提供所需运行时组件：**主题值转换器**（命名空间 `VeloxDev.DynamicTheme`，把 `[ThemeConfig]` 的原始参数转换为平台值）与**过渡类型**（命名空间 `VeloxDev.TransitionSystem` —— 适配器 `Interpolator`、`TransitionEffect` 及 `TransitionEffects` 预设）。本页覆盖主题示例所用到的适配器（`VeloxDev.WPF`、`VeloxDev.Avalonia`），并汇总其余适配器提供的转换器集合。

> 证据：源码 `Src/Adapters/VeloxDev.WPF/PlatformAdapters/**`、`Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/**`；示例 `Examples/Theme/WPF/Demo`、`Examples/Theme/Avalonia/Demo`。

## 命名空间：`VeloxDev.TransitionSystem` — 切换辅助

### 类：`Interpolator`（适配器）

`public class Interpolator : InterpolatorCore`

适配器对 `InterpolatorCore` 的子类，其静态构造函数注册框架的采样器（每个都映射到一个 `ISampler` 实现，如 `BrushSampler`）。它就是要传给 `ThemeManager.SetPlatformInterpolator` 的实例：

```csharp
// 来源：Demo（Examples/Theme/WPF/Demo/App.xaml.cs）
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

| 适配器 | 注册的属性类型 |
|---|---|
| WPF（`VeloxDev.WPF`） | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D` |
| Avalonia（`VeloxDev.Avalonia`） | `IBrush`、`ITransform`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows`、`GridLength` |

#### Interpolator.CreateScheduler

**签名：**
`public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)`

这就是带动画的主题切换所要经过的接缝：`ThemeManager` 按目标向适配器的插值器索取调度器。重写必须返回用 `TransitionSchedulerCore<...>.FindOrCreate(target)` 构建的调度器——只有那条路径会把它登记到目标名下，而后续的 `Transition.Pause` / `Seek` / `Exit` 正是靠它找到这个动画——并且必须对其它平台优先级类型的效果返回 `null`。

```csharp
// 来源：Src/Adapters/VeloxDev.WPF/PlatformAdapters/Interpolator.cs
public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)
    => effect is ITransitionEffect<DispatcherPriority>
        ? (TransitionSchedulerCore)TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>.FindOrCreate(target)
        : null;
```

| 适配器 | 重写接受的优先级 | 构建的调度器 |
|---|---|---|
| WPF、Avalonia、Jalium | `DispatcherPriority` | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>` |
| WinUI | `DispatcherQueuePriority` | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherQueuePriority>` |
| MAUI、WinForms、Razor | `NonPriority` | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, NonPriority>` |

**说明：**
- 每个适配器都提供该重写；各自声明自己的 `UIThreadInspector` 与 `TransitionInterpreter`。
- 基类 `InterpolatorCore.CreateScheduler` 返回 `null`，所以一个不重写它的适配器会让每次主题切换都成为瞬时切换，而不是带动画。

### 类：`TransitionEffect`

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>`

适配器效果，将 `Priority` 重写为 `DispatcherPriority.Render`。从引擎基类继承 `FPS`（60）、`Duration`、`IsAutoReverse`、`LoopTime`、`Ease`、生命周期事件及 `Clone()`。

### 静态类：`TransitionEffects`

| 成员 | 值 |
|---|---|
| `Empty` | `TransitionEffect`，`Duration = TimeSpan.Zero` |
| `Theme` | `TransitionEffect`，`Duration = TimeSpan.FromSeconds(0.46)` |
| `Hover` | `TransitionEffect`，`Duration = TimeSpan.FromSeconds(0.32)` |

**说明：**
- `TransitionEffects.Theme` 是 Trimmed 主题示例传给 `ThemeManager.Transition<T>` 做带动画切换的效果（`Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`，`ReverseThemeWithAnimation`）。完整示例则自建 `new TransitionEffect { Duration = TimeSpan.FromSeconds(3), FPS = 60 }`。
- `ThemeManager.Jump<T>` 做瞬时切换，既不需要效果，也不需要已注册的插值器。
- 这些成员是 `{ get; set; }` 属性而非 `readonly` 字段，因此调用方可以替换预设。

## 命名空间：`VeloxDev.DynamicTheme` — 主题值转换器

所有转换器都实现 `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`。它们定义在适配器程序集（引用核心接口）中、位于同一 `VeloxDev.DynamicTheme` 命名空间下，因此被装饰类可以在 `ThemeManager` 旁边以不加限定的名字引用它们。WPF 实现位于 `Src/Adapters/VeloxDev.WPF/PlatformAdapters/ThemeValueConverters.cs`，Avalonia 实现位于 `Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/ThemeValueConverters.cs`。

| 转换器 | 用途 | 可接受的参数（WPF / Avalonia） |
|---|---|---|
| `DoubleConverter` | `double` 值 | `double` / `int` / `float`，或可固定区域性解析的 `string`。 |
| `PointConverter` | 平台 `Point` | `"x,y"` 字符串（WPF 手工切分，Avalonia 调 `Point.Parse`），或 `[x, y]` 数值。 |
| `ThicknessConverter` | 平台 `Thickness` | uniform / `"h,v"` / `"l,t,r,b"` 字符串，或 1 / 2 / 4 个数值参数。 |
| `CornerRadiusConverter` | 平台 `CornerRadius` | uniform / `"tl,tr,br,bl"` 字符串，或 1 / 4 个数值参数。 |
| `ColorConverter` | 平台 `Color` | 颜色名/HEX 字符串、ARGB `int`，或 A/R/G/B 分量。 |
| `BrushConverter` | 平台画刷 | 现有画刷（WPF 为 `Brush`，Avalonia 为 `IBrush`）、资源键、颜色字符串，或委托给 `ColorConverter` 的结果再包成纯色画刷。 |
| `ObjectConverter` | 任意 `targetType` | 单个资源键字符串；回退到平台类型转换器（`TypeDescriptor` / `TypeUtilities`）。 |

**说明：**
- WPF 面向 `System.Windows` / `System.Windows.Media` 类型，颜色字符串经 `System.Windows.Media.BrushConverter` 解析；资源查找走共享的 `internal` 辅助类 `ThemeResourceLookup`，它遍历 `Application.Current.Resources` 及其合并字典。
- Avalonia 面向 Avalonia 类型（`IBrush`、`Point` 等），字符串经平台类型原生解析器（`Point.Parse`、`Color.TryParse` 等）解析，优先使用 `Avalonia.Utilities.TypeUtilities.TryConvert`，资源经 `Application.Current.TryFindResource` 查找。
- WPF 示例用 `[ThemeConfig<BrushConverter, Light, Dark>(...)]` 标注属性；Avalonia 示例用 `ObjectConverter` + `[ThemeConfig<ObjectConverter, Dark, Light>(...)]`。
- 转换器就是 `ThemeConfigAttribute<TConverter, ...>` 引用的策略（`TConverter`），并在主题登记时由主题生成器实例化。

### 其余适配器中的转换器

其余框架适配器也在各自的 `ThemeValueConverters.cs` 中复刻同一模式（均在命名空间 `VeloxDev.DynamicTheme`）：`VeloxDev.MAUI` 与 `VeloxDev.WinUI` 提供相同的七个转换器；`VeloxDev.WinForms` 提供十三个（`DoubleConverter`、`IntConverter`、`FloatConverter`、`PointConverter`、`PointFConverter`、`SizeConverter`、`SizeFConverter`、`RectangleConverter`、`RectangleFConverter`、`PaddingConverter`、`ColorConverter`、`FontConverter`、`ObjectConverter`）；`VeloxDev.Razor` 提供四个（`DoubleConverter`、`StringConverter`、`IntConverter`、`BoolConverter`）。`VeloxDev.Jalium` 没有提供任何 DynamicTheme 层。这些适配器层均为*推断所得*——它们未被 WPF/Avalonia 示例或测试所执行。

## 相关

- 各框架的 `Transition`/`State`/`UIThreadInspector` 形态属于过渡动画功能的 adapter-provided 章节（`2_API/03_transition`），完整适配器目录属于平台适配器功能（`2_API/08_platform-adapters`）。
