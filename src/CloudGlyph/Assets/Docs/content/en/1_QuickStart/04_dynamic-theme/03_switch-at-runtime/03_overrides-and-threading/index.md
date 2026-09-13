# Dynamic Theme — Runtime Overrides & Threading

## 1. Override a value for one theme

The generated API also lets you override, per instance and per theme, the value that a `[ThemeConfig]` row declared:

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

Source: `Examples/Theme/WPF/Demo/MainWindow.xaml.cs`, members `OnEditThemeValue` and `OnRestoreThemeValue`; the Avalonia demo's handlers take `object?` and are otherwise the same. The context array is the same shape a `[ThemeConfig]` row takes, so `["#fff4d6"]` goes back through the row's own converter.

`SetThemeValue<T>` records the override in the instance's **active** cache and re-applies the property immediately if `T` is the theme currently in use; otherwise the override is picked up the next time a switch to `T` runs. `RestoreThemeValue<T>` removes it, falling back to the declared value. Active values outrank static ones whenever a switch resolves a start or end value.

## 2. Inspect the two caches

`GetStaticThemeCache()` and `GetActiveThemeCache()` return the declared and the overridden resources of the instance. Both use the same generated shape, which the demo's own comment documents:

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

Source: `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`, member `ThemeValueEx` (the same block is in the Avalonia trimmed demo). `ThemeManager` reads exactly these two caches when it prepares a switch: for each property it prefers the active cache entry for the theme and falls back to the static one.

**Expected result:** while `Light` is current, the override is visible on the window immediately; `RestoreThemeValue` returns the property to its declared `Light` value; the property appears in the active cache only after it was overridden.

## 3. Which thread a switch writes on

**Frames are marshalled; preparation is not.** A theme switch is an ordinary transition run, so every *frame*'s property write goes through the adapter's `UIThreadInspector`, which derives the owning dispatcher from the target itself — WPF's inspector resolves a `DispatcherObject` target to that object's own `Dispatcher` and falls back to `Application.Current.Dispatcher`, then queues each write to it (`Src/Adapters/VeloxDev.WPF/PlatformAdapters/UIThreadInspector.cs`, member `ProtectedInvoke`).

The synchronous part of `ThemeManager.Transition` does **not** go through the inspector though: it reads the start values, resolves the schedulers and writes the start values back onto the targets (`ThemeManager.WriteStartValues` uses the compiled property setter directly). Since that part runs on the calling thread, start a switch over UI elements from the UI thread.

Working from the UI thread also keeps the effect's own callbacks there: the sampling loop's awaitable captures the `SynchronizationContext` current when the loop started, so a loop begun on the UI thread resumes there each frame. `Jump` likewise writes with the compiled setter on the calling thread — call it from the UI thread for UI-bound properties.

One more asymmetry worth knowing: in `StartModel.Reflect` mode the start value is read with `PropertyInfo.GetValue(target)` while the switch is being prepared, again on the calling thread. `StartModel.Cache`, the default, reads the cache instead and has no such read.

**Expected result:** a switch started from a UI event updates the element's mapped properties on the UI thread, and `Jump` called from the same handler applies its values synchronously before the handler returns.
