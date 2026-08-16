# 动态主题 — 快速入门

## 动态主题

动态主题为基于 VeloxDev 的编辑器带来**带动画过渡的运行时主题切换**。你通过 `[ThemeConfig]` 在控件或视图模型上声明各主题下的属性值，然后在运行时于 `Light` 与 `Dark` 之间切换 —— 平滑（`Transition<T>`）或即时（`Jump<T>`）。属性值由 TransitionSystem 引擎逐帧插值，而平台适配器提供值转换器与 `Interpolator`。

> 证据：示例项目 `Examples/Theme/WPF/Demo` 与 `Examples/Theme/Avalonia/Demo`，以及测试套件 `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`。

### 快速开始

#### 1. 前置条件

- **支持目标**（来自 `VeloxDev.Core.csproj`、`VeloxDev.WPF.csproj`、`VeloxDev.Avalonia.csproj`）：核心 `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`；WPF 适配器 `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`；Avalonia 适配器 `netstandard2.0` / `net6.0`。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK；示例的特性参数用了 C# 12 集合表达式（需 `LangVersion` 12 / SDK 8.0+）—— *被验证过*的示例说明，非库要求。
- **包管理器：** NuGet / `dotnet` CLI。
- **必需服务：** 与你的 GUI 框架匹配的 UI 适配器 —— `VeloxDev.WPF` 或 `VeloxDev.Avalonia` —— 以及其 `Interpolator`（来自 `VeloxDev.TransitionSystem`），用于带动画的主题切换。


#### 2. 安装 / 添加依赖

添加核心包以及与你 GUI 框架匹配的适配器。值转换器与平台 `Interpolator` 都位于适配器中，因此实践中只需引用适配器即可（WPF 示例正是通过项目引用 `VeloxDev.WPF` 实现的）。

```bash
dotnet add package VeloxDev.Core      # 核心引擎：ThemeManager、ThemeCache、[ThemeConfig]、……
dotnet add package VeloxDev.WPF       # WPF   适配器（Avalonia 则用 VeloxDev.Avalonia）
```

**Expected result：** 包出现在你的 `.csproj` 的 `<ItemGroup>` 中，且 `dotnet restore` 以退出码 0 结束。

#### 3. 基本设置 / 注册

用 `[ThemeConfig<...>]` 装饰你的控件或视图模型类，然后在 `InitializeComponent()` **之后**调用源生成器生成的 `InitializeTheme()`。若需要带动画的切换，还需安装适配器的 `Interpolator`，并选择动画起始模型。

```csharp
public partial class MainWindow
{
    private void LoadTheme()
    {
        InitializeTheme(); // 必须晚于 InitializeComponent() 调用

        // 仅当需要带动画的主题切换时才需要配置插值器
        ThemeManager.SetPlatformInterpolator(new Interpolator());

        // 动画起始状态：从缓存取（Cache），还是反射读取当前属性值（Reflect）
        ThemeManager.StartModel = StartModel.Cache;
    }
}
```

`VeloxDev.Generators.Theme` 源生成器会把类上的每个 `[ThemeConfig]` 转换为 `IThemeObject` 实现：它会向 `ThemeCache` 注册该类、调用 `ThemeManager.Register(this)` 并应用当前主题的值。

**Expected result：** 实例被 `ThemeManager` 注册；默认情况下 `ThemeManager.Current == typeof(Dark)`（由 `ThemeBasicsTests.ThemeManager_DefaultCurrent_IsDark` 验证）。

#### 4. 核心用法（逐步）

**第 1 步 — 声明各主题的值。** 每个 `[ThemeConfig]` 将「一个属性」映射为「每个主题下的一个值」。泛型参数为 `<TConverter, TTheme1, TTheme2, ...>`；属性名之后的数组按顺序对应每个主题的值。

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
{
    // 其余成员见下文第 2 步、第 3 步以及「完整代码」
}
```

**Expected result：** 生成器在类上生成 `IThemeObject` 实现（`InitializeTheme`、`SetThemeValue<T>`、回调等）；该类可被 `ThemeManager` 注册。

**第 2 步 — 带动画切换。** 属性值会按效果的时长与缓动曲线逐帧插值。

```csharp
private static void ReverseThemeWithAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    else
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
}
```

**Expected result：** 窗口背景/前景在 `TransitionEffects.Theme`（`Duration = 0.46 秒`，60 FPS）内平滑变化，随后触发 `OnThemeChanged`。

**第 3 步 — 即时切换。** 无插值；每个属性直接设置为目标主题的值。

```csharp
private static void ReverseThemeWithOutAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Jump<Light>();
    else
        ThemeManager.Jump<Dark>();
}
```

**Expected result：** 主题立即切换、无动画；`OnThemeChanged` 以 `(oldValue, newValue)` 触发。

#### 5. 验证

运行主题示例（`Examples/Theme/WPF/Demo` 或 `Examples/Theme/Avalonia/Demo`）并点击主题切换按钮：

- 使用 `Transition<T>` 时窗口背景/前景会**平滑**变化（`TransitionEffects.Theme` 效果以 60 FPS 运行 0.46 秒）。
- 使用 `Jump<T>` 时切换**立即**完成。
- 每次切换后，生成的 `partial void OnThemeChanged(Type? oldValue, Type? newValue)` 会触发（WPF 示例中弹出一个消息框）。
- 通过 `SetThemeValue<Light>(nameof(Background), ...)` 的运行时覆盖会立即生效；`RestoreThemeValue<Light>` 恢复为主题默认值。

#### 6. 完整代码

一个最小的、完整的 WPF 示例 —— 代码隐藏文件 `MainWindow.xaml.cs`（命名空间 `Demo`）。配套的 `MainWindow.xaml` 声明一个 `Window`，其中包含一个 `Button Click="ChangeTheme"`，并通过 `RelativeSource AncestorType=Window` 绑定 `Background`/`Foreground`：

```csharp
using System.Windows;
using VeloxDev.DynamicTheme;
using VeloxDev.TransitionSystem;

namespace Demo
{
    [ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
    [ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            LoadTheme();
        }

        private void ChangeTheme(object sender, RoutedEventArgs e)
        {
            ReverseThemeWithAnimation();
        }

        private void LoadTheme()
        {
            InitializeTheme();
            ThemeManager.SetPlatformInterpolator(new Interpolator());
            ThemeManager.StartModel = StartModel.Cache;
        }

        partial void OnThemeChanged(Type? oldValue, Type? newValue)
        {
            MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
        }

        private void ReverseThemeWithAnimation()
        {
            if (ThemeManager.Current == typeof(Dark))
                ThemeManager.Transition<Light>(TransitionEffects.Theme);
            else
                ThemeManager.Transition<Dark>(TransitionEffects.Theme);
        }

        private void ReverseThemeWithOutAnimation()
        {
            if (ThemeManager.Current == typeof(Dark))
                ThemeManager.Jump<Light>();
            else
                ThemeManager.Jump<Dark>();
        }
    }
}
```

> **提示：** Avalonia 示例结构相同，但使用 `ObjectConverter`，主题顺序为 `Dark, Light`，并通过 `RelativeSource AncestorType=views:MainWindow` 绑定。上面的完整代码以 `Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 为蓝本。

#### 7. 运行声明

- ⚠️ 未实际运行 —— 仅静态验证。已完整阅读示例源码与测试（`Examples/Theme/WPF/Demo`、`Examples/Theme/Avalonia/Demo`、`Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`），但作者未在本次会话中编译并执行该示例。
