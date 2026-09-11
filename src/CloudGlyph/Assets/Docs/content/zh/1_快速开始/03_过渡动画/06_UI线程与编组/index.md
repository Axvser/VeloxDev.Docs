# Transition — UI线程与编组

## 1. 为何关心 UI 线程

GUI 框架只允许在元素的 **UI 线程**上写属性。因此引擎独立运行其计时/采样循环，把每一帧交给适配器的 `UIThreadInspector`，由它把真正的 `SetValue` 写入分发到所属线程。结果是：**你可以从任意线程启动动画**（包括在 `Task.Run` 内），写入仍落在 UI 线程 —— 编组目标由被动画对象本身推导得出。

具体检查器在各适配器中同名 `UIThreadInspector`（命名空间 `VeloxDev.TransitionSystem`），并自动接进该适配器的 `Transition<T>` 构建器。WPF/Avalonia 与 WinUI 的检查器带分发*优先级*（`DispatcherPriority` / `DispatcherQueuePriority`）；MAUI、WinForms 与 Razor 用 `NonPriority` 填优先级类型参数，走普通无优先级管线。

## 2. 各适配器行为

| 适配器 | UI 绑定目标（`DependencyObject` / `Control` 等） | 普通（非 UI）目标 | 显式捕获 |
|---|---|---|---|
| WPF | 经目标自身 `Dispatcher` 编组 | `Application.Current.Dispatcher` | 无 —— 后台启动即可 |
| Avalonia | 编组到 `Dispatcher.UIThread` | `Dispatcher.UIThread` | 无 |
| MAUI | `Application.Current.Dispatcher.Dispatch(...)` | 同一调度器 | 无 |
| WinUI 3 | 目标自身 `DispatcherQueue` | 惰性捕获的全局队列 | 后台线程首次启动非 UI 目标时 `UIThreadInspector.CaptureUIThread()` |
| WinForms | 目标 `Control`（`BeginInvoke` / `Invoke`） | 惰性捕获的 `WindowsFormsSynchronizationContext` | 可选：`Application.Run` 前 `UIThreadInspector.CaptureUIThread()` |
| Blazor（Razor） | 回路 `SynchronizationContext` | 同一上下文 | 允许后台启动时在 `OnInitialized` 调 `UIThreadInspector.CaptureUIThread()` |

所有适配器也会在首次于 UI 线程触碰时**惰性捕获**全局上下文，因此只有当后台线程首次启动一个无法自证线程的目标时才需要显式捕获。

## 3. 推荐模式

**在 UI 线程启动（总是安全）：**

```csharp
private void OnLoaded(object sender, RoutedEventArgs e)
{
    Animation0.Execute(rect);   // 默认互斥，在 UI 线程启动
}
```

**从后台线程启动（仍会编组）：** 示例正是用 `Task.Run` 这么做的：

```csharp
_ = Task.Run(() =>
{
    Animation0.Execute(rect);              // WPF/Avalonia/WinUI/MAUI/WinForms：可行
    Animation0.Execute(rect, CanMutualTask: false);
});
```

对普通目标无法自证线程的两个适配器，先在 UI 线程捕获一次：

```csharp
// WinUI —— 在 UI 线程（如在 MainWindow 构造函数）；仅当后台线程启动非 DependencyObject
// 目标时才需要。DependencyObject 目标会经自身 DispatcherQueue 编组。
UIThreadInspector.CaptureUIThread();

// Blazor（Razor）—— 在回路线程；Blazor 示例在 OnInitialized 中调用它。
protected override void OnInitialized()
{
    UIThreadInspector.CaptureUIThread();
    base.OnInitialized();
}
```

Blazor 示例是 POCO 目标的参照：它动画一个普通 `BoxModel`（double/`string` 属性），并订阅 `INotifyPropertyChanged` → `InvokeAsync(StateHasChanged)` 来重渲染。

**预期结果：** 从后台线程启动的动画更新 UI 属性时不会抛出跨线程/跨调度器异常，因为每帧写入都由适配器的 `UIThreadInspector` 编组。来自 WinUI 示例的一个告诫：请在 UI 线程构建 `Transition<>` 实例（后台线程使用静态字段可能触发类型初始化问题），或按上面先捕获。

下一步：[验证与完整代码](../07_验证与完整代码/index.md)。
