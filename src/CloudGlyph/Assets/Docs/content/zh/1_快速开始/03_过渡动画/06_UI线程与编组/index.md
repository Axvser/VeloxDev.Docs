# 过渡动画 — UI 线程与编组

## 1. 为什么 UI 线程重要

GUI 框架只允许在元素的 **UI 线程**上写属性。因此引擎独立运行计时 / 采样循环，并把每一帧交给适配器的**宿主**，由它在所属线程上派发真正的 `SetValue` 写入。结果是：**你可以从任意线程启动动画**（包括在 `Task.Run` 内），写入仍会落到 UI 线程 —— 编组目标从被动画对象自身推导。

宿主随每个适配器以 `UIThreadInspector` 之名提供（命名空间 `VeloxDev.TransitionSystem`），并自动接入该适配器的 `Transition<T>`。它是 `TransitionHostBase<TPriorityCore>` 的子类，后者实现 `ITransitionHost<TPriorityCore>` —— 引擎索取的整个宿主面：

| 成员 | 它回答的问题 |
|---|---|
| `ThreadFor(target)` / `IsCurrent(target)` | 哪个线程拥有目标，以及调用方是否已在那个线程上 |
| `Post(target, action, priority)` | 排入一次帧写入；**`false` 表示未排队** |
| `Post(target, thread, action, priority)` | 同上，用于运行已钉住的线程 |
| `PostAsync(target, action, priority)` | 排队并在执行后完成（用于每次动画那一次 `Awake`） |
| `Run<T>(target, body)` | 在目标线程上运行一次读取并返回结果 |
| `IsAlive` | 宿主是否仍在运行（过期帧守卫） |

WPF/Avalonia/Jalium 与 WinUI 宿主携带派发*优先级*（`DispatcherPriority` / `DispatcherQueuePriority`）；MAUI、WinForms 与 Razor 没有调度器优先级，把该类型参数填为 `NonPriority`。

## 2. 各适配器行为

| 适配器 | UI 绑定目标（`DependencyObject` / `Control` 等） | 普通（非 UI）目标 | 显式捕获 |
|---|---|---|---|
| WPF | 经目标自己的 `Dispatcher` 编组 | `Application.Current.Dispatcher` | 无 —— 后台启动可用 |
| Avalonia | 编组到 `Dispatcher.UIThread` | `Dispatcher.UIThread` | 无 |
| MAUI | 目标有自己的 `BindableObject.Dispatcher` 时用它 | `Application.Current?.Dispatcher` | 无 |
| WinUI 3 | 目标自己的 `DispatcherQueue` | 惰性捕获的全局队列 | 非 UI 目标从后台线程启动时用 `UIThreadInspector.CaptureUIThread()` |
| WinForms | 目标 `Control`（`BeginInvoke` / `Invoke`） | 惰性捕获的 `WindowsFormsSynchronizationContext` | 可选：`Application.Run` 之前 `UIThreadInspector.CaptureUIThread()` |
| Blazor (Razor) | 回路 `SynchronizationContext` | 同一上下文 | 在 `OnInitialized` 中 `UIThreadInspector.CaptureUIThread()`，允许后台启动 |

WinUI、WinForms 与 Razor 宿主还会在首次于 UI 线程被触达时**惰性捕获**全局上下文，因此显式捕获只需用于「无法识别自己线程的目标第一次从后台线程启动」。WPF、Avalonia 与 MAUI 则从目标或 `Application.Current` 解析 dispatcher。`ThreadFor` 从不为调用线程现造 dispatcher，也从不抛异常：它回答 `ThreadRef.None`，代价只是该目标失去 UI 线程帧节拍器（循环随后等默认线程池定时器）。

## 3. 推荐模式

**在 UI 线程上启动（总是安全）：**

```csharp
private void OnLoaded(object sender, RoutedEventArgs e)
{
    Animation0.Execute(rect);   // default mutual, started on the UI thread
}
```

**从后台线程启动（仍会被编组）：** demo 正是用 `Task.Run` 这样做：

```csharp
_ = Task.Run(() =>
{
    Animation0.Execute(rect);              // WPF/Avalonia/WinUI/MAUI: fine
    Animation0.Execute(rect, CanMutualTask: false);
});
```

对于普通目标无法推断线程的适配器，先在 UI 线程捕获一次：

```csharp
// WinUI — on the UI thread (e.g. in MainWindow ctor); needed only for non-DependencyObject targets
// started from a background thread. DependencyObject targets marshal through their own DispatcherQueue.
UIThreadInspector.CaptureUIThread();

// Blazor (Razor) — on the circuit thread; the Blazor demo calls this in OnInitialized.
protected override void OnInitialized()
{
    UIThreadInspector.CaptureUIThread();
    base.OnInitialized();
}
```

Blazor demo 是 POCO 目标的参考：它动画一个普通 `BoxModel`（double / `string` 属性），并通过订阅 `INotifyPropertyChanged` → `InvokeAsync(StateHasChanged)` 重渲染。

**预期结果：** 从后台线程启动的动画更新 UI 属性时不会抛 `CrossThreadAccess` / 跨 dispatcher 异常，因为每次帧写入都由适配器宿主编组。WinUI demo 有一个注意点：在 UI 线程上构建 `Transition<>` 实例（从后台线程使用静态字段可能触发类型初始化器问题），或按上面先捕获。`AUTO TEST` 用例 `ObservationSurface_IsReachableAndTicking` 与 `LoadModes` 的「后台线程加载让目标动起来」在每个平台验证两个入口。

下一步：[时间层](../07_时间层/index.md) 下降一层，直接驱动时钟。
