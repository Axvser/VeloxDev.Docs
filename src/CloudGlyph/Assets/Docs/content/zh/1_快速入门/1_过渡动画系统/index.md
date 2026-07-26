# 过渡动画系统 — 快速入门

VeloxDev 过渡动画系统是一个跨平台的属性动画引擎。它提供了插值器、缓动函数、状态快照和调度器，用于在属性值之间创建平滑的动画过渡。

## 安装

过渡动画系统属于 `VeloxDev.Core`：

```xml
<PackageReference Include="VeloxDev.Core" Version="6.0.82" />
```

## 基本用法

### 1. 创建状态快照

状态快照捕获一个或多个属性的当前值，并定义它们的动画目标值。

```csharp
using VeloxDev.TransitionSystem.Abstractions;

// 为特定目标类型创建状态快照
var state = TransitionCore<MyControl, StateSnapshotCore<MyControl>>.Create();

// 配置属性过渡
state.Property<double>(ctrl => ctrl.Opacity)
	.To(0.5)              // 目标值
	.Duration(300)         // 持续时间（毫秒）
	.Ease(Eases.Sine.Out); // 缓动函数
```

### 2. 执行过渡

```csharp
// 将过渡应用到目标对象
TransitionCore<MyControl, StateSnapshotCore<MyControl>>
	.Execute(myControl, state);

// 或使用扩展方法
state.Execute(myControl);
```

### 3. 平台设置（Avalonia 示例）

每个平台适配器都提供了平台特定的插值器。在启动时注册一次：

```csharp
// 在 App.axaml.cs 或 Program.cs 中
using VeloxDev.DynamicTheme;

// 注册 Avalonia 插值器
ThemeManager.SetPlatformInterpolator(new VeloxDev.Avalonia.Interpolator());
```

### 4. 多属性动画

```csharp
var snapshot = TransitionCore<MyControl, StateSnapshotCore<MyControl>>.Create();

// 同时动画多个属性
snapshot.Property<double>(ctrl => ctrl.Opacity)
	.To(0.0)
	.Duration(500)
	.Ease(Eases.Quad.In);

snapshot.Property<double>(ctrl => ctrl.Width)
	.To(300)
	.Duration(1000)
	.Ease(Eases.Elastic.Out);

snapshot.Property<Brush>(ctrl => ctrl.Background)
	.To(new SolidColorBrush(Colors.Red))
	.Duration(300);

// 一次性执行
snapshot.Execute(myControl);
```

### 5. 使用调度器

为了更好地控制时间和生命周期，使用 `TransitionScheduler`：

```csharp
using VeloxDev.TransitionSystem.Abstractions;

var scheduler = new TransitionSchedulerCore();

// 调度过渡
scheduler.Add(snapshot, myControl);
scheduler.Start();

// 稍后...
scheduler.Pause();
scheduler.Resume();
scheduler.Exit();  // 停止所有过渡
```

## 缓动函数

VeloxDev 通过 `Eases` 静态类提供全面的缓动函数集合：

| 类别 | 函数 |
|---|---|
| Sine | `Eases.Sine.In`, `.Out`, `.InOut` |
| Quad | `Eases.Quad.In`, `.Out`, `.InOut` |
| Cubic | `Eases.Cubic.In`, `.Out`, `.InOut` |
| Quart | `Eases.Quart.In`, `.Out`, `.InOut` |
| Quint | `Eases.Quint.In`, `.Out`, `.InOut` |
| Expo | `Eases.Expo.In`, `.Out`, `.InOut` |
| Circ | `Eases.Circ.In`, `.Out`, `.InOut` |
| Back | `Eases.Back.In`, `.Out`, `.InOut` |
| Elastic | `Eases.Elastic.In`, `.Out`, `.InOut` |
| Bounce | `Eases.Bounce.In`, `.Out`, `.InOut` |

## 原生插值器

`VeloxDev.TransitionSystem.NativeInterpolators` 中的内置插值器：

| 类型 | 插值器 |
|---|---|
| `double` | `DoubleInterpolator` |
| `float` | `FloatInterpolator` |
| `int` | `IntInterpolator` |
| `long` | `LongInterpolator` |
| `System.Drawing.Point` | `PointInterpolator` |
| `System.Drawing.PointF` | `PointFInterpolator` |
| `System.Drawing.Size` | `SizeInterpolator` |
| `System.Drawing.SizeF` | `SizeFInterpolator` |
| `System.Drawing.Rectangle` | `RectangleInterpolator` |
| `System.Drawing.RectangleF` | `RectangleFInterpolator` |
| `System.Numerics.Vector2` | `Vector2Interpolator` |
| `System.Numerics.Vector3` | `Vector3Interpolator` |
| `System.Numerics.Vector4` | `Vector4Interpolator` |
| `System.Numerics.Quaternion` | `QuaternionInterpolator` |
| `System.Drawing.Color` | `ColorInterpolator` |

## 自定义插值器

实现 `IValueInterpolator` 以添加自定义类型支持：

```csharp
public class MyCustomInterpolator : IValueInterpolator
{
	public IList<object?> Interpolate(object? from, object? to, int steps)
	{
		// 生成中间值
	}
}

// 全局注册
InterpolatorCore.RegisterInterpolator(typeof(MyType), new MyCustomInterpolator());
```

## 进一步阅读

- 查看 [API 参考](../../2_API参考/1_过渡动画系统/index.md) 了解详细接口文档
- 查看 [动态主题](../2_动态主题/index.md) 快速入门了解主题动画集成
