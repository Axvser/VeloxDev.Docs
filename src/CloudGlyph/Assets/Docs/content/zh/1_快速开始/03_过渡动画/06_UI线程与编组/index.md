# 过渡动画 — UI 线程与编组

## 1. 为什么 UI 线程重要

GUI 框架只允许在元素的 **UI 线程**上写属性。因此引擎独立地跑它的计时/采样循环，并把每一帧交给适配器的**宿主**，由它把真正的 `SetValue` 写入派发到所属线程。结果是：**你可以从任意线程启动动画**（包括 `Task.Run` 里），写入仍然落在 UI 线程 —— 编组目标是从被动画的对象本身推出来的。

宿主随每个适配器以 `UIThreadInspector` 之名提供（命名空间 `VeloxDev.TransitionSystem`），并自动接进该适配器的 `Transition<T>`。它是 `TransitionHostBase<TPriorityCore>` 的子类，后者实现 `ITransitionHost<TPriorityCore>` —— 引擎索取的整个宿主面：

| 成员 | 它回答的问题 |
|---|---|
| `ThreadFor(target)` / `IsCurrent(target)` | 目标属于哪个线程，调用方是否已在上面 |
| `Post(target, action, priority)` | 排入一次帧写入；**返回 `false` 表示没排进去** |
| `Post(target, thread, action, priority)` | 同上，但面向该趟已钉死的线程 |
| `PostAsync(target, action, priority)` | 排入并在它运行后完成（用于每个动画唯一那次 `Awake`） |
| `Run<T>(target, body)` | 在目标线程上做一次读取并返回结果 |
| `IsAlive` | 宿主是否还在运行（过期帧守卫） |

WPF/Avalonia/Jalium 与 WinUI 的宿主携带派发*优先级*（`DispatcherPriority` / `DispatcherQueuePriority`）；MAUI、WinForms 与 Razor 没有调度器优先级，把那个类型形参填为 `NonPriority`。

## 2. 各适配器行为

| 适配器 | UI 绑定目标（`DependencyObject` / `Control` 等） | 普通（非 UI）目标 | 显式捕获 |
|---|---|---|---|
| WPF | 经目标自己的 `Dispatcher` 编组 | `Application.Current.Dispatcher` | 无 —— 后台启动可用 |
| Avalonia | 编组到 `Dispatcher.UIThread` | `Dispatcher.UIThread` | 无 |
| MAUI | 目标自己的 `BindableObject.Dispatcher`（若有） | `Application.Current?.Dispatcher` | 无 |
| WinUI 3 | 目标自己的 `DispatcherQueue` | 惰性捕获的全局队列 | 非 UI 目标从后台线程启动时用 `UIThreadInspector.CaptureUIThread()` |
| WinForms | 目标 `Control`（`BeginInvoke` / `Invoke`） | 惰性捕获的 `WindowsFormsSynchronizationContext` | 可选，`Application.Run` 之前 `UIThreadInspector.CaptureUIThread()` |
| Blazor（Razor） | 回路 `SynchronizationContext` | 同一上下文 | 为允许后台启动，在 `OnInitialized` 里 `UIThreadInspector.CaptureUIThread()` |

所有宿主还会在首次被 UI 线程触碰时**惰性捕获**全局上下文，因此显式捕获只在「一个无法识别自身线程的目标第一次从后台线程启动」时才需要。`ThreadFor` 绝不为调用线程现造 dispatcher，也绝不抛异常：它回答 `ThreadRef.None`，那只是让该目标失去 UI 线程帧节奏器（循环随后等默认线程池定时器）。

## 3. 推荐写法

**在 UI 线程上启动（永远安全）：**

```csharp
private void OnLoaded(object sender, RoutedEventArgs e)
{
    Animation0.Execute(rect);   // 默认互斥，在 UI 线程上启动
}
```

**从后台线程启动（仍被编组）：** 演示正是这么做的：

```csharp
_ = Task.Run(() =>
{
    Animation0.Execute(rect);              // WPF/Avalonia/WinUI/MAUI：没问题
    Animation0.Execute(rect, CanMutualTask: false);
});
```

对那些普通目标无法推断线程的适配器，先在 UI 线程上捕获一次：

```csharp
// WinUI —— 在 UI 线程上（例如 MainWindow 构造函数里）；只有非 DependencyObject 目标
// 从后台线程启动时才需要。DependencyObject 目标经自己的 DispatcherQueue 编组。
UIThreadInspector.CaptureUIThread();

// Blazor（Razor）—— 在回路线程上；Blazor 演示在 OnInitialized 里调用它。
protected override void OnInitialized()
{
    UIThreadInspector.CaptureUIThread();
    base.OnInitialized();
}
```

Blazor 演示是 POCO 目标的参照：它动画一个普通 `BoxModel`（double/`string` 属性），并通过订阅 `INotifyPropertyChanged` → `InvokeAsync(StateHasChanged)` 重渲染。

**预期结果：** 从后台线程启动的动画更新 UI 属性时不抛 `CrossThreadAccess` / 跨 dispatcher 异常，因为每一帧写入都由适配器宿主编组。WinUI 演示给出一条注意事项：在 UI 线程上构建 `Transition<>` 实例（静态字段从后台线程使用可能撞上类型初始化问题），或照上面先捕获。`AUTO TEST` 用例 `ObservationSurface_IsReachableAndTicking` 与 `LoadModes` 的「后台线程加载让目标动起来」在每个平台上核验了两个入口。

下一步：[时间层](../07_时间层/index.md) 下沉一层，直接驱动时钟。
