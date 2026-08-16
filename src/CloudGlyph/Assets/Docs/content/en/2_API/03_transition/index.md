# Transition — API Reference

The engine lives in `VeloxDev.Core` (`VeloxDev.TransitionSystem` + `.Abstractions`); each platform adapter (WPF/Avalonia/WinUI/MAUI/WinForms/Razor) exposes the same public shapes in the `VeloxDev.TransitionSystem` namespace with its own `Interpolator`, `TransitionEffect`, `UIThreadInspector`, and native interpolators.

Every member below is verified against source and, where noted, against `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` and `Examples/Transition/*`.

## API — Sections

This feature's API reference is split into:

- `00_transitionsystem/`
- `01_abstractions/`
- `02_nativeinterpolators/`
- `03_adapter-provided/`
- `04_timeline/`
