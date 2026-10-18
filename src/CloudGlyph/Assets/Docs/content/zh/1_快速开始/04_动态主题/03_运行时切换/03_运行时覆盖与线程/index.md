# 动态主题 — 运行时覆盖与线程

## 1. 为某个主题覆盖一个值

生成的 API 还允许你按实例、按主题覆盖某行 `[ThemeConfig]` 声明的值：

```csharp
private void OnEditThemeValue(object sender, RoutedEventArgs e)
    => SetThemeValue<Light>(nameof(Background), new object?[] { "#fff4d6" });

private void OnRestoreThemeValue(object sender, RoutedEventArgs e)
    => RestoreThemeValue<Light>(nameof(Background));
```

来源：`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的 `OnEditThemeValue` 与 `OnRestoreThemeValue`；Avalonia 示例的同名处理器形参为 `object?`，其余相同。

`SetThemeValue<T>` 把值**原样**存进该实例的**活动**缓存 —— 生成的方法不会对它调用 `TConverter`。请传入属性本身期望的类型（例如 `Background` 用 `Brush`）；示例里的原始上下文数组 `["#fff4d6"]` 会被当作数据存储，重新应用时因不可赋值给该属性而被跳过。随后 `UpdatePropertyToCurrentTheme` 会按当前主题重新应用该属性，因此为其他主题准备的覆盖会在下一次切到 `T` 时生效。`RestoreThemeValue<T>` 移除该属性的条目（所有主题）并回退到声明值。切换在解析起点或终点时，活动值始终优先于静态值。

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

**预期结果：** 该属性只有在被覆盖之后才出现在活动缓存中；当存储的值可赋值给该属性且该主题正是当前主题时，覆盖立即可见；`RestoreThemeValue` 让属性回到声明的当前主题值。

## 3. 切换写在哪个线程

**帧写入会被编组，准备阶段不会。** 一场主题切换就是普通的过渡 run，所以每个*帧*的属性写入都经过适配器的 `UIThreadInspector`，它从目标自身推导所属 dispatcher —— WPF 的 inspector 把 `DispatcherObject` 目标解析成它自带的 `Dispatcher`，回退到 `Application.Current?.Dispatcher ?? Dispatcher.FromThread(Thread.CurrentThread)`，并通过 `Dispatcher.InvokeAsync` 把每帧写入排到该 dispatcher 上（`Src/Adapters/VeloxDev.WPF/PlatformAdapters/UIThreadInspector.cs` 的 `ThreadFor` 与 `PostCore`）。

但 `ThemeManager.Transition` 的同步部分**不**经过 inspector：它读取起点、解析 scheduler，并把起点写回目标（`ThemeManager.WriteStartValues` 直接用编译好的属性 setter）。既然这部分在调用线程上运行，面向 UI 元素的切换请从 UI 线程发起。

采样循环本身**不会**被钉在 UI 线程上：它的自定义 awaiter 不恢复 `SynchronizationContext`，因此在 UI 线程上启动的循环可能在第一帧之后转到线程池线程，除非宿主提供了 pacer。这样做是安全的，因为每次*写入*都经宿主（`SamplerSet.Apply`）编组；但 effect 的 `Update` / `LateUpdate` 回调可能在该线程上运行。`Jump` 同样用编译好的 setter 在调用线程上写值 —— 对 UI 绑定属性请从 UI 线程调用它。

还有一处值得知道的不对称：`StartModel.Reflect` 模式下，起点是在准备切换时用 `PropertyInfo.GetValue(target)` 读的，同样在调用线程上。默认档 `StartModel.Cache` 读的是缓存，没有这次读取。

**预期结果：** 从 UI 事件发起的切换会在 UI 线程上更新元素的已映射属性；在同一个处理器里调用 `Jump`，会在处理器返回之前同步应用其值。
