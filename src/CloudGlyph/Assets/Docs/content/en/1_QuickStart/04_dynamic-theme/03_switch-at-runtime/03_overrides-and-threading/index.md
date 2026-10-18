# Dynamic Theme — Runtime Overrides & Threading

## 1. Override a value for one theme

The generated API also lets you override, per instance and per theme, the value that a `[ThemeConfig]` row declared:

```csharp
private void OnEditThemeValue(object sender, RoutedEventArgs e)
    => SetThemeValue<Light>(nameof(Background), new object?[] { "#fff4d6" });

private void OnRestoreThemeValue(object sender, RoutedEventArgs e)
    => RestoreThemeValue<Light>(nameof(Background));
```

Source: `Examples/Theme/WPF/Demo/MainWindow.xaml.cs`, members `OnEditThemeValue` and `OnRestoreThemeValue`; the Avalonia demo's handlers take `object?` and are otherwise the same.

`SetThemeValue<T>` stores the value **verbatim** in the instance's **active** cache — the generated method does not run `TConverter` on it. Pass the type the property itself expects (for `Background`, a `Brush`); a raw context array such as the demo's `["#fff4d6"]` is stored as data, and the re-apply write is skipped when it is not assignable to the property. Then `UpdatePropertyToCurrentTheme` re-applies the property for the theme that is current, so an override for another theme is picked up the next time a switch to `T` runs. `RestoreThemeValue<T>` removes the property's entry (all themes) and falls back to the declared value. Active values outrank static ones whenever a switch resolves a start or end value.

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

**Expected result:** the property appears in the active cache only after it was overridden; an override whose stored value is assignable to the property and whose theme is current is visible immediately; `RestoreThemeValue` returns the property to its declared current-theme value.

## 3. Which thread a switch writes on

**Frames are marshalled; preparation is not.** A theme switch is an ordinary transition run, so every *frame*'s property write goes through the adapter's `UIThreadInspector`, which derives the owning dispatcher from the target itself — WPF's inspector resolves a `DispatcherObject` target to that object's own `Dispatcher`, falling back to `Application.Current?.Dispatcher ?? Dispatcher.FromThread(Thread.CurrentThread)`, and posts each write through `Dispatcher.InvokeAsync` (`Src/Adapters/VeloxDev.WPF/PlatformAdapters/UIThreadInspector.cs`, `ThreadFor` and `PostCore`).

The synchronous part of `ThemeManager.Transition` does **not** go through the inspector though: it reads the start values, resolves the schedulers and writes the start values back onto the targets (`ThemeManager.WriteStartValues` uses the compiled property setter directly). Since that part runs on the calling thread, start a switch over UI elements from the UI thread.

The sampling loop itself is **not** pinned to the UI thread: its custom awaiter does not restore a `SynchronizationContext`, so a loop begun on the UI thread can resume on a pool thread after its first frame unless the host supplied a pacer. That is safe because every *write* is marshalled through the host (`SamplerSet.Apply`), but the effect's `Update` / `LateUpdate` callbacks may run on that thread. `Jump` likewise writes with the compiled setter on the calling thread — call it from the UI thread for UI-bound properties.

One more asymmetry worth knowing: in `StartModel.Reflect` mode the start value is read with `PropertyInfo.GetValue(target)` while the switch is being prepared, again on the calling thread. `StartModel.Cache`, the default, reads the cache instead and has no such read.

**Expected result:** a switch started from a UI event updates the element's mapped properties on the UI thread, and `Jump` called from the same handler applies its values synchronously before the handler returns.
