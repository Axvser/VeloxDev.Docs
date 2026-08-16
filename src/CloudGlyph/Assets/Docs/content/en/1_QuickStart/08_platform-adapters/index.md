# Platform Adapters — Quick Start

## Platform Adapters

### Quick Start

VeloxDev ships six GUI adapters — **WPF**, **Avalonia**, **WinUI**, **MAUI**, **WinForms** and **Razor (Blazor)** — each in its own package (`VeloxDev.WPF`, `VeloxDev.Avalonia`, `VeloxDev.WinUI`, `VeloxDev.MAUI`, `VeloxDev.WinForms`, `VeloxDev.Razor`). An adapter is the thin layer that turns the UI-framework-agnostic workflow engine into a real, interactive editor: it provides the attached behaviors that drive the surface, the object-pooled view container, the minimap/grid overlay interfaces, and the per-platform transition and theme wiring (`Interpolator`, `TransitionEffects`, `ThemeValueConverters`, `UIThreadInspector`).

A `dotnet new` item-template suite (`VeloxDev.WPF.Templates` and sibling packages) scaffolds the Node / Slot / Link / Tree / selector / grid-decorator / minimap-overlay views with the behaviors already connected.

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages:

- `00_prerequisites/`
- `01_install/`
- `02_setup/`
- `03_core-usage/`
- `04_verification/`
- `05_complete-code/` — the complete scaffold, one page per source file
