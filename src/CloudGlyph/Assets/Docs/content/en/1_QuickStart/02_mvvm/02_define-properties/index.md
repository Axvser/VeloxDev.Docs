# MVVM — Define Observable Properties

`[VeloxProperty]` is a marker attribute (`AttributeTargets.Field | AttributeTargets.Property`) with no parameters. The generator rewrites the marked member into a public observable property plus `partial` hook declarations, and only synthesizes the notification infrastructure that is not already present in the class hierarchy.

## 1. Field form (works on every supported target)

Mark a private field; the property name is derived by capitalizing the field name (`_count` → `Count`, `_greeting` → `Greeting`):

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private int _count;
}
```

The generator (`MVVMWriter`) emits the property and hook declarations into a partial part of the same class. For the field above the generated setter body is:

```csharp
public int Count
{
    get => _count;
    set
    {
        if (global::System.Object.Equals(_count, value)) return;
        var old = _count;
        OnPropertyChanging(nameof(Count));
        OnCountChanging(old, value);
        _count = value;
        OnCountChanged(old, value);
        OnPropertyChanged(nameof(Count));
    }
}

partial void OnCountChanging(int oldValue, int newValue);
partial void OnCountChanged(int oldValue, int newValue);
```

You then implement the hooks in your own file with a `partial` method of the same signature:

```csharp
public partial class CounterViewModel
{
    partial void OnCountChanged(int oldValue, int newValue)
    {
        System.Console.WriteLine($"[hook] Count {oldValue} -> {newValue}");
    }
}
```

**Expected result:** `_count` is exposed as `public int Count`; assigning `Count = 5` runs (1) `OnPropertyChanging(nameof(Count))` → raises `PropertyChanging`, (2) `partial OnCountChanging(old, new)`, (3) the field assignment, (4) `partial OnCountChanged(old, new)` → prints `[hook] Count 0 -> 5`, (5) `OnPropertyChanged(nameof(Count))` → raises `PropertyChanged`. Assigning the same value again short-circuits at the `Object.Equals` guard — no events, no hook calls.

## 2. Partial-property form (C# 13)

Declare a C# 13 partial property instead of a field. The generator supplies the implementing accessors and a backing field named `_<name>`:

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] public partial string Greeting { get; set; }
}
```

This is real usage — `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpServerConfiguration.cs` annotates all of its configuration members this way with no base class and no boilerplate.

**Expected result:** the same public property, backing field and `OnGreetingChanging` / `OnGreetingChanged` hooks are generated; the class needs no manual `INotifyPropertyChanged` implementation.

## 3. Notification infrastructure is auto-detected per class

`MVVMWriter` inspects the whole hierarchy before generating:

- **No base provides it** → the generator adds `INotifyPropertyChanging` / `INotifyPropertyChanged` to the class and emits `public event PropertyChangingEventHandler? PropertyChanging;`, `public event PropertyChangedEventHandler? PropertyChanged;`, `public virtual void OnPropertyChanging(string propertyName)` and `public virtual void OnPropertyChanged(string propertyName)` (the events are raised by these methods).
- **A base already provides events/methods** (e.g. the demos' own `ObservableViewModelBase`, which implements the interfaces and declares `OnPropertyChanging(string)` / `OnPropertyChanged(string)`) → the generator reuses them and does **not** emit duplicates.
- **A well-known MVVM base is detected** and the generated setter delegates to that framework's own notifier instead of poking events directly: CommunityToolkit.Mvvm `ObservableObject`/`[ObservableObject]` and Prism `BindableBase` → `SetProperty(...)`, ReactiveUI `ReactiveObject` → `RaiseAndSetIfChanged(...)`, Caliburn.Micro `PropertyChangedBase` → `NotifyOfPropertyChange(...)`. This lets VeloxDev properties live inside an existing MVVM view-model base you already use.

**Expected result:** a bare `partial class` compiles to a type that satisfies `INotifyPropertyChanging` and `INotifyPropertyChanged`; a class deriving from a base that already implements them gains only the annotated properties and hooks — the observable behavior of subscribing to the events is identical in both cases.

## 4. Where the generated code goes

One `.g.cs` file per annotated class, named `{ClassName}_{Namespace_With_Underscores}_MVVM.g.cs`, e.g. `CounterViewModel_QuickStart_Mvvm_MVVM.g.cs` (method `GetFileName()` in `Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs`). Two classes in the same namespace produce two files — generation is per class.

**Expected result:** after building, the file appears under `obj/<Configuration>/<TargetFramework>/generated/`; double-clicking it in the IDE shows the property, the hooks and (only when needed) the notification members above.

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. Generated shapes are transcribed from `Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs` (`MVVMPropertyFactory.GenerateViewModel`, setter-body builders) and `MVVMWriter.cs`; the partial-property example is real code from `McpServerConfiguration.cs`.
