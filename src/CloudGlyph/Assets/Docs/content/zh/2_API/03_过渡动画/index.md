# Transition — API 参考

引擎位于 `VeloxDev.Core`（`VeloxDev.TransitionSystem` + `.Abstractions`）；每个平台适配器（WPF/Avalonia/WinUI/MAUI/WinForms/Razor）在 `VeloxDev.TransitionSystem` 命名空间中暴露相同的公共形态，并自带 `Interpolator`、`TransitionEffect`、`UIThreadInspector` 与原生采样器。

下面每个成员都依据源码验证，并在标注处依据 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` 与 `Examples/Transition/*`。

## API — Sections

This feature's API reference is split into:

- `00_transitionsystem/`
- `01_abstractions/`
- `02_nativesamplers/`
- `03_adapter-provided/`
- `04_timeline/`
