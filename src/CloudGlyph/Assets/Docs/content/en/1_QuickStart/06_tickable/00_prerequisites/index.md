# 00 · Prerequisites

## Supported targets

These come from the library's declared `TargetFrameworks`, not from what the demo happens to run on. `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` declares:

```text
netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0
```

Any target that can consume one of those can use the feature. The demo (`Examples/Tickable/WPF/Demo/Demo.csproj`) targets `net10.0-windows` with `<UseWPF>true</UseWPF>` — that is one *tested* configuration, not the minimum.

| What | Requirement |
|---|---|
| Library target frameworks | `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0` |
| Package version | `VeloxDev.Core` 10.0.0 |
| Generator package | `VeloxDev.Core.Generator` 10.0.0 (analyzer only, not referenced at runtime) |
| SDK / runtime | Any SDK that can build one of the target frameworks above; the walkthrough in this guide uses the .NET 10 SDK against `net10.0` |
| IDE / editor | Optional — the generator runs inside `dotnet build` |
| Services | **None.** No UI adapter, no service host, no configuration file |

## The one hard requirement: `partial`

The source generator writes its half of the class into a separate file, so the class you mark must be declared `partial`. This is a compile-time requirement with a compile-time error — there is nothing to configure.

```csharp
[Tickable]
public partial class MyBehaviour   // <- `partial` is mandatory
{
}
```

## No UI thread is required

The pumps run on their own background threads (or on `async` tasks in async-loop mode). A console `Main`, a unit test, a service host and a WPF window are all equally valid hosts. A GUI host does **not** get free marshalling: a hook runs on a pump thread, so anything that touches UI must be handed back to the UI thread by you — either through `TickManager.ExecuteOnMainThread` or by publishing state that the UI thread polls (which is what the WPF demo does; see `Examples/Tickable/WPF/Demo/MainWindow.xaml.cs`).

## Platform note for browser and iOS

`TickManager.UseAsyncLoop` defaults to `true` when `OperatingSystem.IsBrowser()` or `OperatingSystem.IsIOS()` reports true, because those runtimes cannot start dedicated `Thread`s. On the `net5.0`-and-later targets, every other runtime defaults to `false` (native threads); on the `netstandard2.0`, `netframework4.6.1` and `netcoreapp3.0` targets the `OperatingSystem` API does not exist, so the initializer falls back to `true` there too. You can override it globally through the property or per channel through `SetUseAsyncLoop`.

**Expected result:** you can name the framework you will build for and you have an SDK that supports it. Nothing has been installed yet.
