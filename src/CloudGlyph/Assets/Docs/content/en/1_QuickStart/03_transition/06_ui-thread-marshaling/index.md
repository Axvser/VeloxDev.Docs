# Transition — UI Thread & Marshaling

## 1. Why the UI thread matters

A GUI framework only allows property writes on the element's **UI thread**. The engine therefore runs its timing/sampling loop independently and hands every frame to the adapter's **host**, which dispatches the actual `SetValue` writes on the owning thread. The result is that **you may start an animation from any thread** (including inside `Task.Run`) and the writes still land on the UI thread — the marshaling target is derived from the animated object itself.

The host lives with each adapter under the name `UIThreadInspector` (namespace `VeloxDev.TransitionSystem`) and is wired automatically into that adapter's `Transition<T>`. It is a subclass of `TransitionHostBase<TPriorityCore>`, which implements `ITransitionHost<TPriorityCore>` — the whole host surface the engine asks for:

| Member | Question it answers |
|---|---|
| `ThreadFor(target)` / `IsCurrent(target)` | which thread owns the target, and whether the caller is already on it |
| `Post(target, action, priority)` | queue a frame write; **`false` means it was not queued** |
| `Post(target, thread, action, priority)` | the same, for a thread the run already pinned |
| `PostAsync(target, action, priority)` | queue it and complete once it has run (used for the one `Awake` per animation) |
| `Run<T>(target, body)` | run a read on the target's thread and return its result |
| `IsAlive` | whether the host is still running (the stale-frame guard) |

WPF/Avalonia/Jalium and WinUI hosts carry a dispatch *priority* (`DispatcherPriority` / `DispatcherQueuePriority`); MAUI, WinForms and Razor have no dispatcher priority and fill that type parameter with `NonPriority`.

## 2. Per-adapter behavior

| Adapter | UI-bound target (`DependencyObject` / `Control` / etc.) | Plain (non-UI) target | Explicit capture |
|---|---|---|---|
| WPF | marshals through the target's own `Dispatcher` | `Application.Current.Dispatcher` | none — background starts work |
| Avalonia | marshals to `Dispatcher.UIThread` | `Dispatcher.UIThread` | none |
| MAUI | the target's own `BindableObject.Dispatcher` when it has one | `Application.Current?.Dispatcher` | none |
| WinUI 3 | the target's own `DispatcherQueue` | the lazily-captured global queue | `UIThreadInspector.CaptureUIThread()` for non-UI targets started from a background thread |
| WinForms | the target `Control` (`BeginInvoke` / `Invoke`) | lazily captured `WindowsFormsSynchronizationContext` | optional `UIThreadInspector.CaptureUIThread()` before `Application.Run` |
| Blazor (Razor) | the circuit `SynchronizationContext` | same context | `UIThreadInspector.CaptureUIThread()` in `OnInitialized` to allow background starts |

All hosts also **lazily capture** the global context the first time they are touched on the UI thread, so explicit capture is only ever needed for the first start from a background thread of a target that cannot identify its own thread. `ThreadFor` never mints a dispatcher for the calling thread and never throws: it answers `ThreadRef.None`, which merely costs that target its UI-thread frame pacer (the loop then waits on the default thread-pool timer).

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
    Animation0.Execute(rect);              // WPF/Avalonia/WinUI/MAUI: fine
    Animation0.Execute(rect, CanMutualTask: false);
});
```

For the adapters whose plain targets cannot infer a thread, capture once on the UI thread first:

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

**Expected result:** an animation started from a background thread updates the UI property without a `CrossThreadAccess` / cross-dispatcher exception, because every frame write is marshaled by the adapter's host. One caveat from the WinUI demo: build the `Transition<>` instance on the UI thread (a static field used from a background thread may hit a type-initializer issue), or capture first as above. The `AUTO TEST` case `ObservationSurface_IsReachableAndTicking` and the `LoadModes` case "后台线程加载让目标动起来" verify both entry points on every platform.

Next: [Timing Layer](../07_timing-layer/index.md) drops one level below all of this and drives the clock directly.
