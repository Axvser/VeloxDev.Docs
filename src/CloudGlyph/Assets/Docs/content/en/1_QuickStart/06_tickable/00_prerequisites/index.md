# Prerequisites

## Supported targets

These come from the library's declared `TargetFrameworks`, not from what the demo happens to run on. `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` declares:

```text
netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0
```

Any project that can consume one of those can use the feature. The demo (`Examples/Tickable/WPF/Demo/Demo.csproj`) targets `net10.0-windows` with `<UseWPF>true</UseWPF>` — that is one *tested* configuration, not the minimum.

| What | Requirement |
|---|---|
| Library target frameworks | `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`, `net8.0` |
| Package version | `VeloxDev.Core` 10.0.0 |
| Generator package | `VeloxDev.Core.Generator` 10.0.0 (analyzer only, not referenced at runtime) |
| SDK / runtime | Any SDK that can build one of the target frameworks above; the walkthrough uses the .NET 10 SDK |
| Generator compiler | Roslyn 4.8+ — the generator is compiled against `Microsoft.CodeAnalysis.CSharp` 4.8.0, so use the .NET 8 SDK or later (or VS 2022 17.8+). The package's `.targets` emits `VELOXCFG0001` on a Roslyn below 4.0 |
| IDE / editor | Optional — the generator runs inside `dotnet build` |
| Services | **None.** No UI adapter, no service host, no configuration file |

## The one hard requirement: `partial`

The source generator writes its half of the class into a separate file, so the class you mark must be declared `partial`. This is a compile-time requirement with no configuration.

```csharp
[Tickable]
public partial class MyBehaviour   // <- `partial` is mandatory
{
}
```

## No UI thread is required

The pumps run on their own background threads (or on `async` tasks in async-loop mode). A console `Main`, a unit test, a service host and a WPF window are all equally valid hosts. A GUI host does **not** get free marshalling: a hook runs on a pump thread, so anything that touches UI must be handed back to the UI thread by you — either through `TickManager.ExecuteOnMainThread` (which targets the channel's update thread, not the UI thread) or by publishing state that the UI thread polls, which is what the WPF demo does (`Examples/Tickable/WPF/Demo/MainWindow.xaml.cs`).

## Platform note for browser and iOS

`TickManager.UseAsyncLoop` initialises from the build target (`TickManager.cs` lines 1008-1013):

```csharp
public static bool UseAsyncLoop { get; set; } =
#if NET5_0_OR_GREATER
    OperatingSystem.IsBrowser() || OperatingSystem.IsIOS();
#else
    true;
#endif
```

On the `net5.0`-and-later targets it starts `true` only when the process runs in a browser or on iOS, and `false` on every other runtime (native threads). On `netstandard2.0`, `netframework4.6.1` and `netcoreapp3.0` the `OperatingSystem` API is unavailable, so the initializer falls back to `true`. A `netstandard2.0` consumer running on desktop .NET therefore gets the async loop unless it sets the property. Override it globally through the property or per channel through `SetUseAsyncLoop`.

**Expected result:** you can name the framework you will build for and you have an SDK that supports it. Nothing has been installed yet.
