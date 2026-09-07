# Dynamic Theme — Install & Add Dependency

## 1. Add the engine core

The theme engine ships in `VeloxDev.Core`. Adding it also brings in `VeloxDev.Core.Generator` — the build-time source generator that turns a `[ThemeConfig]`-decorated `partial` class into an `IThemeObject` implementation:

```bash
dotnet add package VeloxDev.Core
```

**Expected result:** the package appears in the `.csproj`; after restore `using VeloxDev.DynamicTheme;` compiles, so `ThemeManager`, `ThemeCache`, `[ThemeConfig]`, `ITheme`, `Dark` and `Light` resolve.

## 2. Add the platform adapter for UI values

Applying the theme values to real UI elements — and animating between them — needs the adapter for your GUI framework. The adapter ships the per-framework **theme value converters** (`BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter`) and the `Interpolator` + `TransitionEffects` used by animated switches:

```bash
dotnet add package VeloxDev.WPF       # WPF
dotnet add package VeloxDev.Avalonia  # Avalonia
```

The adapter packages belong to VeloxDev's Platform Adapters suite; each one references `VeloxDev.Core`, so referencing only the adapter package is sufficient in practice (the WPF demo references the `VeloxDev.WPF` project alone).

**Expected result:** `BrushConverter` is usable as the `[ThemeConfig]` converter type, and under `VeloxDev.TransitionSystem` the adapter's `Interpolator` and `TransitionEffects.Theme` resolve.

## 3. In-repo alternative (Debug project references)

When building against the repository source instead of NuGet, reference only the adapter project — the demos do exactly that:

```xml
<ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Adapters\VeloxDev.WPF\VeloxDev.WPF.csproj" />
</ItemGroup>
```

The adapter project references the `VeloxDev.Core` **project** in `Debug` (and the `VeloxDev.Core` **NuGet package** in `Release`), so the theme engine and the source generator flow transitively into your project.

**Expected result:** the project restores and builds; a `[ThemeConfig]`-decorated `partial` class gains the generated `IThemeObject` members at compile time.
