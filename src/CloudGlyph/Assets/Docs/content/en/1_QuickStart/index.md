# Quick Start

Hands-on guides for every VeloxDev feature. Each page takes you from an empty project to a **working program**, step by step, with the exact SDK/runtime versions, an observable **Expected result** under every step, and an honest **Run Declaration** at the end.

VeloxDev is a set of .NET libraries for building **AI-controllable workflow editors** on any .NET GUI. Start with the core workflow engine, then layer on MVVM, animation, theming, AOP, the MonoBehaviour loop, and the AI agent.

| Feature | What you will build |
|---|---|
| [00 Workflow System](00_workflow-system) | A node graph on a canvas: tree, nodes, slots, links, undo/redo, compile & run |
| [01 Workflow Agent](01_workflow-agent) | An AI that edits the workflow at runtime via 60+ tools and MCP servers |
| [02 MVVM](02_mvvm) | Observable properties and async commands via source generators |
| [03 Transition](03_transition) | Fluent property interpolation and easing |
| [04 Dynamic Theme](04_dynamic-theme) | Runtime theme switching with animated transitions |
| [05 AOP](05_aop) | Compile-time aspect proxies |
| [06 MonoBehaviour](06_monobehaviour) | Frame-driven lifecycle loop |
| [07 Weak Types](07_weak-types) | Weak collections and delegates |
| [08 Platform Adapters](08_platform-adapters) | GUI adapters and `dotnet new` view templates |

## Prerequisites (common to all pages)

- .NET SDK **8.0.400+** (examples target `net9.0`; the libraries multi-target `netstandard2.0` / `net6.0` / `net9.0`).
- A supported GUI workload installed for the adapter you pick (WPF / Avalonia / WinUI / MAUI / WinForms / Razor).
- NuGet access to restore `VeloxDev.*` packages.
