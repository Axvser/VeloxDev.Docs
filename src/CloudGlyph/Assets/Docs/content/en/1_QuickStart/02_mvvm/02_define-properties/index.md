# MVVM — Define Observable Properties

`[VeloxProperty]` (`AttributeTargets.Field | AttributeTargets.Property`, no parameters, not sealed) marks a member that `VeloxDev.Generators.MVVM` rewrites into an observable property.

## 1. Field form

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private int _count;
}
```

The property name drops a leading `_` and upper-cases the next character (`_count` → `Count`). The emitted property is:

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if(global::System.Object.Equals(this._count, value)) return;
        var old = this._count;
        OnPropertyChanging(nameof(Count));
        OnCountChanging(old, value);
        this._count = value;
        OnCountChanged(old, value);
        OnPropertyChanged(nameof(Count));
    }
}
partial void OnCountChanging(System.Int32 oldValue, System.Int32 newValue);
partial void OnCountChanged(System.Int32 oldValue, System.Int32 newValue);
```

Implement the hooks in another part of the same class. Because the generator declares them, an incorrect signature is a compile error rather than a silently ignored method.

```csharp
public partial class CounterViewModel
{
    partial void OnCountChanged(int oldValue, int newValue)
    {
        System.Console.WriteLine($"[count] {oldValue} -> {newValue}");
    }
}
```

**Expected result:** `Count = 3` raises `PropertyChanging`, calls `OnCountChanging`, assigns the field, calls `OnCountChanged` (printing `[count] 0 -> 3`), then raises `PropertyChanged`. Assigning the same value again short-circuits at the equality guard: no events, no hooks.

## 2. Partial-property form (C# 13)

```csharp
[VeloxProperty] public partial string Greeting { get; set; }
```

The generator supplies the accessors and a backing field named `_greeting`, and preserves the access modifiers and accessor visibility you declared. A property that is not `partial` cannot be completed; the generator reports `VELOX_MVVM_PROP003` and skips it.

**Expected result:** the same `Greeting` property and `OnGreetingChanging` / `OnGreetingChanged` hooks are generated.

## 3. Notification infrastructure is detected per class

Before emitting, the writer inspects the class and its bases:

- **Nothing supplied** → the type receives `INotifyPropertyChanging` / `INotifyPropertyChanged`, the `PropertyChanging` / `PropertyChanged` events, and `OnPropertyChanging(string)` / `OnPropertyChanged(string)`.
- **A base already supplies them** (for example the demos' `ObservableViewModelBase`) → the generator emits no duplicates and the setters call the inherited methods.
- **A known framework base is detected** → the generated setter delegates to that framework's notifier: CommunityToolkit.Mvvm and Prism (`SetProperty(ref T, T, string)`), ReactiveUI (`RaiseAndSetIfChanged`), Caliburn.Micro (`NotifyOfPropertyChange`).

**Expected result:** a bare `partial class` compiles into a type implementing both notification interfaces; a class deriving from a base that already implements them gains only the annotated property and hooks. Subscribing to the events behaves identically.

## 4. Diagnostics and generated files

| Diagnostic | Severity | Condition |
| --- | --- | --- |
| `VELOX_MVVM_PROP001` | Error | two members map to the same property name, or an existing field cannot back the property (const/static/read-only, or a different type) |
| `VELOX_MVVM_PROP002` | Warning | the field name yields no valid identifier |
| `VELOX_MVVM_PROP003` | Warning | the annotated property is not `partial`, so its accessors cannot be completed |

One file per class: `{ClassName}_{Namespace_With_Underscores}_MVVM.g.cs`. It appears under `obj/<Configuration>/<TargetFramework>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/` when the build passes `-p:EmitCompilerGeneratedFiles=true`.

**Expected result:** a bad declaration reports the diagnostic id on the author's own line; a good one produces one generated file per class.

## Run declaration

- ⚠️ Not actually run in this documentation pass — statically verified against `Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs`, `Base/Analizer.cs` (`MVVMPropertyFactory`) and `Diagnostics.cs`. The emitted setter and hook declarations are transcribed from those templates; the partial-property form is sourced from the writer, not compiled here.
