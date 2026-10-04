# MVVM — Define Observable Properties

`[VeloxProperty]` is a marker attribute (`AttributeTargets.Field | AttributeTargets.Property`) with no parameters. The generator rewrites the marked member into a public observable property plus `partial` hook declarations, and synthesizes only the notification infrastructure the class does not already have.

## 1. Field form (works on every supported target)

Mark a private field; the property name is derived from the field name by dropping a leading `_` and upper-casing the next character (`_count` → `Count`):

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] private int _count;
}
```

The generated code below is the real output for exactly this member (see the Run Declaration for how it was produced):

```csharp
public System.Int32 Count
{
    get => this._count;
    set
    {
        if (global::System.Object.Equals(this._count, value)) return;
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

You implement the hooks in your own part of the class; the generator supplies the declarations, so a mismatched signature is a compile error rather than a silently ignored method:

```csharp
public partial class CounterViewModel
{
    partial void OnCountChanged(int oldValue, int newValue)
    {
        System.Console.WriteLine($"[count] {oldValue} -> {newValue}");
    }
}
```

**Expected result:** `_count` is exposed as `public int Count`. Assigning `Count = 3` runs, in order, (1) `OnPropertyChanging(nameof(Count))` → raises `PropertyChanging`, (2) the `partial OnCountChanging(old, new)` hook, (3) the field assignment, (4) the `partial OnCountChanged(old, new)` hook → prints `[count] 0 -> 3`, (5) `OnPropertyChanged(nameof(Count))` → raises `PropertyChanged`. Assigning the same value again short-circuits at the `Object.Equals` guard: no events, no hooks.

## 2. Partial-property form (C# 13)

Declare a C# 13 partial property instead of a field. The generator supplies the implementing accessors plus a backing field:

```csharp
using VeloxDev.MVVM;

namespace QuickStart.Mvvm;

public partial class CounterViewModel
{
    [VeloxProperty] public partial string Greeting { get; set; }
}
```

This form is used in the repository — `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpServerConfiguration.cs` annotates its configuration members this way, with no base class and no boilerplate.

**Expected result:** the same public property and `OnGreetingChanging` / `OnGreetingChanged` hooks are generated; the class still needs no manual `INotifyPropertyChanged` implementation.

## 3. Notification infrastructure is detected per class

The MVVM writer walks the class and its bases before emitting, and adds only what is missing (this is what the generated file above shows for a bare `partial class`):

- **No base provides it** → the generator puts `INotifyPropertyChanging` / `INotifyPropertyChanged` on the partial class and emits `public event PropertyChangingEventHandler? PropertyChanging;`, `public event PropertyChangedEventHandler? PropertyChanged;`, `public virtual void OnPropertyChanging(string propertyName)` and `public virtual void OnPropertyChanged(string propertyName)`.
- **A base already provides events and methods** (for example the demos' own `ObservableViewModelBase`) → the generator reuses them and emits no duplicates.
- **A well-known MVVM base is recognized** (CommunityToolkit.Mvvm, Prism, ReactiveUI, Caliburn.Micro) → the generated setter delegates to that framework's own notifier (`SetProperty`, `RaiseAndSetIfChanged`, `NotifyOfPropertyChange`) instead of raising the local events.

**Expected result:** a bare `partial class` compiles to a type that satisfies both notification interfaces; a class deriving from a base that already implements them gains only the annotated properties and hooks. Subscribing to the events behaves identically in both cases.

## 4. Where the generated code goes

One file per annotated class, named `{ClassName}_{Namespace_With_Underscores}_MVVM.g.cs` from `GetFileName()` in `Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs`. Generation is per class: two classes in one namespace produce two files.

**Expected result:** after building with `-p:EmitCompilerGeneratedFiles=true`, the file appears under `obj/<Configuration>/<TargetFramework>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/`. Without that switch it is still compiled in, but only visible through the IDE's generated-file node.

## Run declaration

- ✅ Actually built and run on 2026-10-01. A console project in a scratch directory referenced `VeloxDev.Core.csproj` plus `VeloxDev.Core.Generator.csproj` as an analyzer (Debug), declared `[VeloxProperty] private int _count;`, `[VeloxProperty] private ObservableCollection<string> _items = [];` and a `partial void OnCountChanged` hook that prints, and was run with `dotnet run -c Debug`. Recorded output (the first three lines come from this page's members):

  ```text
  [collection] added: ready
  initial: Count=0, CanExecute(Decrement)=False
  Items: ready
  [count] 0 -> 3
  ```

- The generated shapes quoted in sections 1 and 3 are transcribed verbatim from the emitted file `obj/Debug/net9.0/generated/VeloxDev.Core.Generator/VeloxDev.Generators.MVVM/CounterViewModel_QuickStart_Mvvm_MVVM.g.cs` of that same build, not reconstructed by hand. The `partial`-property form in section 2 was not compiled in this pass (it needs C# 13 language level); its claim is sourced from `McpServerConfiguration.cs`.
