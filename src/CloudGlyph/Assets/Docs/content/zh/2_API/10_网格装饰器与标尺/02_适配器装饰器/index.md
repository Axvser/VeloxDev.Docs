# 适配器装饰器

只有 Razor 适配器自带装饰器类型。XAML 适配器提供的是条目模板：生成的类在每个平台上形状相同，只是绘制 API 不同。每家适配器仍通过同一套命名部件或参数契约解析装饰器。

## Razor：WorkflowGridDecorator

```csharp
namespace VeloxDev.WorkflowSystem.AttachedBehaviors;

public partial class WorkflowGridDecorator : ComponentBase, IWorkflowGridDecorator, IDisposable
```

镜像 `WorkflowSurfaceBehavior` 偏移并绘制刻度层的 Razor 组件。

### 参数与属性

| 成员 | 声明 | 特性 | 默认 | 含义 |
|---|---|---|---|---:|
| `Viewport` | `SurfaceViewport? Viewport { get; set; }` | `[Parameter]` | `null` | 行为推送的表面视口上下文。 |
| `ViewportFeed` | `SurfaceViewportFeed? ViewportFeed { get; set; }` | `[CascadingParameter]` | `null` | 组件订阅的 feed，用于廉价的刻度刷新。 |
| `RulerThickness` | `double RulerThickness { get; set; }` | `[Parameter]` | `28` | 标尺厚度（像素）。 |
| `Spacing` | `double Spacing { get; set; }` | `[Parameter]` | `40` | 刻度间距（像素）。 |
| `MajorLineEvery` | `int MajorLineEvery { get; set; }` | `[Parameter]` | `5` | 带标签刻度之间的小格数。 |
| `RulerBackground` | `string RulerBackground { get; set; }` | `[Parameter]` | `"rgba(37,37,38,0.78)"` | 标尺背景色。 |
| `TickColor` | `string TickColor { get; set; }` | `[Parameter]` | `"#555555"` | 刻度色。 |
| `LabelColor` | `string LabelColor { get; set; }` | `[Parameter]` | `"#888888"` | 数字标签色。 |
| `DividerColor` | `string DividerColor { get; set; }` | `[Parameter]` | `"#3A3D40"` | 标尺分隔线色。 |
| `AxisColor` | `string? AxisColor { get; set; }` | `[Parameter]` | `null` | 世界 0 刻度色；回退到 `TickColor`。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | — | `0` | 推送的滚动偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | — | `0` | 推送的内容偏移。 |
| `RulerBand` | `double RulerBand => RulerThickness` | — | — | 只读带厚度。 |

### 生命周期

```csharp
protected override void OnInitialized();
protected override void OnParametersSet();
public void Dispose();
```

`OnInitialized` 订阅 `ViewportFeed.Changed`；`OnParametersSet` 复制推送的偏移并确保刻度窗口；`Dispose` 取消订阅。

标签先按整数格式化，达到 10,000 用 `K`，达到 1,000,000 用 `M`。

## XAML 条目模板

七个包以 `{prefix}-v-decorator` 暴露装饰器条目，前缀为 `wpf`、`ava`、`winui`、`maui`、`winforms`、`razor` 与 `jalium`。WPF 标识是 `VeloxDev.WPF.WorkflowGridDecorator`；源文件是 `TemplateClass.cs`，默认名是 `GridDecorator`。

XAML 平台上生成的类派生自 `Grid` 并实现 `IWorkflowGridDecorator`。公开形状：

| 成员 | 类型 | 默认 |
|---|---|---:|
| `RulerThickness` | `double` | `28` |
| `GridSpacing` | `double` | `40` |
| `MajorLineEvery` | `int` | `5` |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | `0` |
| `ContentOffsetX` / `ContentOffsetY` | `double` | `0` |
| `RulerBand` | `double`（只读） | `RulerThickness` |

模板还参数化表面、次线、主线、轴、标尺、刻度、标签与分隔线的颜色。生成的构造函数会裁剪到边界、创建不参与命中测试的网格层与标尺层、把标尺放在内容上方，并在尺寸变化时让两层失效。

适配器不自带这个类型；每个工程用 `dotnet new <prefix>-v-decorator` 生成一次。

## 各适配器的 GridDecoratorName

| 适配器 | 声明 | 访问器元素类型 |
|---|---|---|
| WPF | `DependencyProperty.RegisterAttached("GridDecoratorName", typeof(string), ...)` | `DependencyObject` |
| Avalonia | `AvaloniaProperty.RegisterAttached<WorkflowSurfaceBehavior, UserControl, string?>("GridDecoratorName")` | `AvaloniaObject` |
| WinUI | `DependencyProperty.RegisterAttached(...)` | `DependencyObject` |
| WinForms | `DependencyProperty.RegisterAttached(...)` | `Control` |
| MAUI | `BindableProperty.CreateAttached(...)` | `BindableObject` |
| Jalium | `DependencyProperty.RegisterAttached(...)` | `DependencyObject` |
| Razor | `[Parameter] public RenderFragment<SurfaceViewport>? GridDecorator { get; set; }` | — |

每个 `GridDecoratorName` 默认都是 `null`。行为在 `UserControl` 命名空间里按名解析元素，只有它实现 `IWorkflowGridDecorator` 时才推送。Razor 改为传一个接收当前 `SurfaceViewport` 的渲染片段。

## 说明

- XAML 平台上装饰器必须包住滚动视图，而不是放在画布内；它需要按视口尺寸绘制并看到滚动偏移。
- Razor 组件从视口 feed 重新渲染刻度层；不需要整面重绘。
- 只在用到该能力时设置名称或片段；表面能容忍缺少装饰器。
