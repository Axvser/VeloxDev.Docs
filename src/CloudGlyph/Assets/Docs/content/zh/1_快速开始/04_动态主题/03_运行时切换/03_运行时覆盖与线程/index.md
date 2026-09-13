# 动态主题 — 运行时覆盖与线程

## 1. 为某个主题覆盖一个值

生成的 API 还允许你按实例、按主题覆盖某行 `[ThemeConfig]` 声明的值：

```csharp
/// <summary>
/// Overrides one value for one theme on this instance, and puts it back. An override beats the declared value
/// for that theme, and only the properties actually changed appear in the active cache.
/// </summary>
private void OnEditThemeValue(object sender, RoutedEventArgs e)
    => SetThemeValue<Light>(nameof(Background), new object?[] { "#fff4d6" });

private void OnRestoreThemeValue(object sender, RoutedEventArgs e)
    => RestoreThemeValue<Light>(nameof(Background));
```

来源：`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的 `OnEditThemeValue` 与 `OnRestoreThemeValue`；Avalonia 示例的同名处理器形参为 `object?`，其余相同。上下文数组与 `[ThemeConfig]` 那一行同形，因此 `["#fff4d6"]` 会经过该行自己的转换器。

`SetThemeValue<T>` 把覆盖记入该实例的**活动**缓存，并且如果 `T` 正是当前使用的主题，就立即重新应用该属性；否则这份覆盖会在下一次切到 `T` 时生效。`RestoreThemeValue<T>` 移除它，回退到声明的值。切换在解析起点或终点时，活动值始终优先于静态值。

## 2. 查看两个缓存

`GetStaticThemeCache()` 与 `GetActiveThemeCache()` 分别返回该实例的声明资源与被覆盖资源。两者使用同一套生成的形状，示例自己的注释就记录了它：

```csharp
/* The "resource" here is a complex auto-generated structure.
   Only modified properties are stored in the dynamic resources; otherwise nothing is stored.
   When the theme switches, dynamic content overrides static content.
   Dictionary<string,Dictionary<PropertyInfo,Dictionary<Type,object?>>>

   From left to right
   string       -> name of property
   PropertyInfo -> target to use theme change
   Type         -> theme
   object?      -> value of property at the theme

   It provides full access to the theme resources.
 */
```

来源：`Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs` 的 `ThemeValueEx`（Avalonia 版示例中有同一段）。`ThemeManager` 在准备切换时读的正是这两个缓存：逐个属性先取活动缓存中该主题的条目，取不到再回退到静态缓存。

**预期结果：** 当 `Light` 为当前主题时，覆盖立即在窗口上可见；`RestoreThemeValue` 让属性回到声明的 `Light` 值；该属性只有在被覆盖之后才出现在活动缓存中。

## 3. 切换写在哪个线程

**帧写入会被编组，准备阶段不会。** 一场主题切换就是普通的过渡 run，所以每个*帧*的属性写入都经过适配器的 `UIThreadInspector`，它从目标自身推导所属 dispatcher —— WPF 的 inspector 把 `DispatcherObject` 目标解析成它自带的 `Dispatcher`，回退到 `Application.Current.Dispatcher`，然后把每帧写入排到该 dispatcher 上（`Src/Adapters/VeloxDev.WPF/PlatformAdapters/UIThreadInspector.cs` 的 `ProtectedInvoke`）。

但 `ThemeManager.Transition` 的同步部分**不**经过 inspector：它读取起点、解析 scheduler，并把起点写回目标（`ThemeManager.WriteStartValues` 直接用编译好的属性 setter）。既然这部分在调用线程上运行，面向 UI 元素的切换请从 UI 线程发起。

从 UI 线程发起还有额外好处：effect 自己的回调也留在那里 —— 采样循环的 awaitable 会捕获循环启动时所在的 `SynchronizationContext`，因此在 UI 线程上启动的循环每帧都回到 UI 线程。`Jump` 同样用编译好的 setter 在调用线程上写值 —— 对 UI 绑定属性请从 UI 线程调用它。

还有一处值得知道的不对称：`StartModel.Reflect` 模式下，起点是在准备切换时用 `PropertyInfo.GetValue(target)` 读的，同样在调用线程上。默认档 `StartModel.Cache` 读的是缓存，没有这次读取。

**预期结果：** 从 UI 事件发起的切换会在 UI 线程上更新元素的已映射属性；在同一个处理器里调用 `Jump`，会在处理器返回之前同步应用其值。
