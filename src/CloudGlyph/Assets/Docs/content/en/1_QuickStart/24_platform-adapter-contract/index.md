# Platform Adapter Contract

VeloxDev.Core owns the surface every GUI adapter closes: one input route, one set of scroll and navigation capabilities, one grid/minimap data exchange, one view-pool composition. The seven adapters in `Src/Adapters/` are implementations of that surface — none of them invents a second one.

This QuickStart follows the contract on a WPF surface built in code, so the shared behaviour can be observed without a window. The same assertions are what the headless conformance kit drives on WPF, Avalonia, WinForms, Razor and Jalium.

## Pages

- [Prerequisites](00_prerequisites/index.md) — supported targets, packages and tooling.
- [Named Parts](01_named-parts/index.md) — the seven roles and the attached-property names that bind them.
- [Surface and Input](02_surface-and-input/index.md) — the input route, the scroller/navigator capabilities, surface metrics and the view pool.
- [Conformance](03_conformance/index.md) — the shared `TestGraph`, a runnable contract test and the headless suites.
