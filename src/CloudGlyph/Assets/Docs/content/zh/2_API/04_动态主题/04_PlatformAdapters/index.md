# API — 动态主题 · 平台适配器

平台适配器（`VeloxDev.WPF` / `VeloxDev.Avalonia`）提供具体的 `Interpolator`、过渡效果以及主题值转换器。下列类型位于命名空间 `VeloxDev.TransitionSystem`（插值器 / 效果）或 `VeloxDev.DynamicTheme`（值转换器）。

> 证据：源码 `Src/Adapters/VeloxDev.WPF/PlatformAdapters/*`、`Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/*`；示例 `Examples/Theme/WPF/Demo`、`Examples/Theme/Avalonia/Demo`。

## 命名空间：`VeloxDev.TransitionSystem`

### 类：`Interpolator`（适配器）

WPF：`public class Interpolator : InterpolatorCore`
Avalonia：`public class Interpolator : InterpolatorCore`

适配器 `Interpolator` 继承自非泛型 `InterpolatorCore`（泛型 `InterpolatorCore<InterpolatorOutput, DispatcherPriority>` 层级随帧序列模型一并移除）。静态构造函数注册平台采样器（均实现 `ISampleable, ISampler`，`Normalize => this` + `Update`）：

| 适配器 | 注册的属性类型 |
|---|---|
| WPF（`VeloxDev.WPF`） | `Brush`、`Thickness`、`Point`、`CornerRadius`、`Transform`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect`、`Point3D`、`Vector3D` |
| Avalonia（`VeloxDev.Avalonia`） | `IBrush`、`ITransform`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows`、`GridLength` |

**说明：**
- 每个注册的类型映射到一个采样器（如 `BrushSampler`、`ThicknessSampler`），存入 `NativeInterpolators`（`ConcurrentDictionary<Type, ISampleable>`）。
- 这是传给 `ThemeManager.SetPlatformInterpolator<T>(T)` 的实例。

### 类：`TransitionEffect`

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>`

| 成员 | 值 |
|---|---|
| `Priority` | `override DispatcherPriority Priority { get; set; } = DispatcherPriority.Render` |

**说明：**
- 从 `TransitionEffectCore` 继承 `FPS`（默认 60）、`Duration`、`IsAutoReverse`、`LoopTime`、`Ease`、生命周期事件及 `Clone()`。

### 静态类：`TransitionEffects`

| 成员 | 值 |
|---|---|
| `Empty` | `Duration = TimeSpan.Zero` |
| `Theme` | `Duration = TimeSpan.FromSeconds(0.46)` |
| `Hover` | `Duration = TimeSpan.FromSeconds(0.32)` |

**说明：**
- `TransitionEffects.Theme` 是主题示例用于带动画切换的效果。

## 命名空间：`VeloxDev.DynamicTheme`

### 值转换器

全部实现 `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`。两个适配器都提供相同的七个转换器；WPF 实现位于 `Src/Adapters/VeloxDev.WPF/PlatformAdapters/ThemeValueConverters.cs`，Avalonia 实现位于 `Src/Adapters/VeloxDev.Avalonia/PlatformAdapters/ThemeValueConverters.cs`。

| 转换器 | 用途 | 可接受的参数 |
|---|---|---|
| `DoubleConverter` | `double` 值 | `double`、`int`、`float`，或可解析的 `string`（固定区域性）。 |
| `PointConverter` | `Point` 值 | `"x,y"` 字符串，或 `[x, y]` 数值。 |
| `ThicknessConverter` | `Thickness` 值 | `"uniform"`、`"h,v"`、`"l,t,r,b"` 字符串，或 1/2/4 个数值参数。 |
| `CornerRadiusConverter` | `CornerRadius` 值 | `"uniform"`、`"tl,tr,br,bl"` 字符串，或 1/4 个数值参数。 |
| `ColorConverter` | `Color` 值 | 颜色名/HEX 字符串、ARGB `int`，或 A/R/G/B 分量。 |
| `BrushConverter` | `Brush` 值 | 现有的 `Brush`、资源键、颜色字符串，或委托给 `ColorConverter` 的结果。 |
| `ObjectConverter` | 任意 `targetType` | 单个资源键字符串；回退到平台类型转换器（`TypeDescriptor`/`TypeUtilities`）。 |

**说明：**
- 转换器就是 `ThemeConfigAttribute<TConverter, ...>` 引用的策略（`TConverter`）。
- Avalonia 示例使用 `ObjectConverter`；WPF 示例使用 `BrushConverter`。
- WPF 转换器通过 `Application.Current.Resources`（及合并字典）进行资源键查找；Avalonia 转换器使用 `Application.Current.TryFindResource`。
