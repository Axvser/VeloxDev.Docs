# Transition — UI Thread & Marshaling

## 1. Why the UI thread matters

A GUI framework only allows property writes on the element's **UI thread**. The engine therefore runs its timing/sampling loop independently and hands every frame to the adapter's `UIThreadInspector`, which dispatches the actual `SetValue` writes on the owning thread. The result is that **you may start an animation from any thread** (including inside `Task.Run`) and the writes still land on the UI thread — the marshaling target is derived from the animated object itself.

The concrete inspector lives with each adapter under the name `UIThreadInspector` (namespace `VeloxDev.TransitionSystem`) and is wired automatically into that adapter's `Transition<T>` snapshot type. WPF/Avalonia and WinUI inspectors carry a dispatch *priority* (`DispatcherPriority` / `DispatcherQueuePriority`); MAUI, WinForms and Razor use the plain non-priority pipeline.

## 2. Per-adapter behavior

| Adapter | UI-bound target (`DependencyObject` / `Control` / etc.) | Plain (non-UI) target | Explicit capture |
|---|---|---|---|
| WPF | marshals through the target's own `Dispatcher` | `Application.Current.Dispatcher` | none — background starts work |
| Avalonia | marshals to `Dispatcher.UIThread` | `Dispatcher.UIThread` | none |
| MAUI | `Application.Current.Dispatcher.Dispatch(...)` | same dispatcher | none |
| WinUI 3 | the target's own `DispatcherQueue` | the lazily-captured global queue | `UIThreadInspector.CaptureUIThread()` for non-UI targets started from a background thread |
| WinForms | the target `Control` (`BeginInvoke` / `Invoke`) | lazily captured `WindowsFormsSynchronizationContext` | optional `UIThreadInspector.CaptureUIThread()` before `Application.Run` |
| Blazor (Razor) | the circuit `SynchronizationContext` | same context | `UIThreadInspector.CaptureUIThread()` in `OnInitialized` to allow background starts |

All adapters also **lazily capture** the global context the first time they are touched on the UI thread, so explicit capture is only ever needed for the first start from a background thread of a target that cannot identify its own thread.

## 3. Recommended patterns

**Start on the UI thread (always safe):**

```csharp
private void OnLoaded(object sender, RoutedEventArgs e)
{
    Animation0.Execute(rect);   // default mutual, started on the UI thread
}
```

**Start from a background thread (still marshaled):** the demos do exactly this with `Task.Run`:

```csharp
_ = Task.Run(() =>
{
    Animation0.Execute(rect);              // WPF/Avalonia/WinUI/MAUI/WinForms: fine
    Animation0.Execute(rect, CanMutualTask: false);
});
```

For the two adapters whose plain targets cannot infer a thread, capture once on the UI thread first:

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

The Blazor demo is the reference for POCO targets: it animates a plain `BoxModel` (double/`string` properties) and re-renders by subscribing `INotifyPropertyChanged` → `InvokeAsync(StateHasChanged)`.

**Expected result:** an animation started from a background thread updates the UI property without a `CrossThreadAccess` / cross-dispatcher exception, because every frame write is marshaled by the adapter's `UIThreadInspector`. One caveat from the WinUI demo: build a `Transition<>` snapshot on the UI thread (a static field used from a background thread may hit a type-initializer issue), or capture first as above.

Next: [Verify & Complete Code](../07_verify-and-complete-code/index.md).
