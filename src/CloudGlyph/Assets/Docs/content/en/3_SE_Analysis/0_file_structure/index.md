# File Structure

## Repository Layout

```
VeloxDev/
├── Src/
│   ├── Core/
│   │   ├── VeloxDev.Core/                 ← Core engine (netstandard2.0, net4.6.1, net5, netcoreapp3.0)
│   │   │   ├── WorkflowSystem/            ← Workflow editing engine
│   │   │   ├── TransitionSystem/          ← Property animation system
│   │   │   ├── DynamicTheme/              ← Dynamic theme switching
│   │   │   ├── MVVM/                      ← MVVM infrastructure
│   │   │   ├── AspectOriented/            ← AOP proxy system
│   │   │   ├── AI/                        ← AI Agent integration
│   │   │   ├── TimeLine/                  ← MonoBehaviour system
│   │   │   ├── WeakTypes/                 ← Weak reference collections
│   │   │   └── Interfaces/                ← Public API interfaces
│   │   ├── VeloxDev.Core.Extension/       ← Optional extensions (AI/MCP/Workflow resources)
│   │   ├── VeloxDev.Core.Test/            ← MSTest unit tests
│   │   └── VeloxDev.Core.Generator/       ← Roslyn source generator
│   ├── Adapters/
│   │   ├── VeloxDev.WPF/                  ← WPF adapter
│   │   ├── VeloxDev.Avalonia/             ← Avalonia adapter
│   │   ├── VeloxDev.WinUI/               ← WinUI adapter
│   │   ├── VeloxDev.MAUI/                ← .NET MAUI adapter
│   │   ├── VeloxDev.WinForms/            ← Windows Forms adapter
│   │   └── VeloxDev.Razor/               ← Blazor/Razor adapter
│   └── Templates/                         ← Project templates
├── Examples/
│   ├── Workflow/                          ← Workflow demos (all platforms)
│   ├── Transition/                        ← Animation demos (all platforms)
│   ├── Theme/                             ← Theme demos
│   ├── MVVM/                              ← MVVM demos
│   ├── AOP/                               ← AOP demos
│   └── MonoBehaviour/                     ← MonoBehaviour demos
├── Docs/
│   └── VeloxDev.Docs/                     ← Wiki documentation (CloudGlyph)
└── Assets/                                ← Shared assets (logo, icons)
```

## Core Module Structure (`VeloxDev.Core`)

```
VeloxDev.Core/
├── Interfaces/WorkflowSystem/      ← Public API contracts
│   ├── IWorkflowTreeViewModel.cs
│   ├── IWorkflowNodeViewModel.cs
│   ├── IWorkflowSlotViewModel.cs
│   ├── IWorkflowLinkViewModel.cs
│   └── ... (helpers, spatial, etc.)
├── WorkflowSystem/                  ← Implementation
│   ├── Anchor.cs / Size.cs / Offset.cs / Viewport.cs / CellKey.cs
│   ├── CanvasLayout.cs / WorkContext.cs / NodeBoundsProvider.cs
│   ├── SpatialGridHashMap.cs       ← Spatial indexing
│   ├── WorkflowSpatialManager.cs   ← Spatial management
│   ├── WorkflowActionPair.cs       ← Undo/redo actions
│   ├── Templates/                  ← Builder attributes + default VMs
│   │   ├── WorkflowBuilder.cs      ← [Tree<T>], [Node<T>], [Slot<T>], [Link<T>]
│   │   ├── ViewModels/             ← Default ViewModel implementations
│   │   └── Helpers/                ← Default Helper implementations
│   ├── StandardEx/                 ← Standard extension methods
│   ├── Compilation/                ← Workflow compiler
│   └── SelectorEx/                 ← Conditional slot selectors
├── TransitionSystem/               ← Animation engine
├── DynamicTheme/                   ← Theme system
├── MVVM/                           ← VeloxCommand, attributes
├── AI/                             ← Agent integration
├── AspectOriented/                 ← AOP
├── TimeLine/                       ← MonoBehaviour
└── WeakTypes/                      ← Weak collections
```

## Adapter Structure (e.g. `VeloxDev.Avalonia`)

```
VeloxDev.Avalonia/
├── Attached/Workflow/              ← XAML attached behaviors
│   ├── WorkflowSurfaceBehavior.cs
│   ├── WorkflowNodeDragBehavior.cs
│   ├── WorkflowSlotConnectionBehavior.cs
│   ├── WorkflowSlotLayoutBehavior.cs
│   ├── WorkflowCanvasTransformBehavior.cs
│   ├── ViewPool.cs / ViewManager.cs
│   └── WorkflowMinimapOverlay.cs
├── PlatformAdapters/               ← Platform-specific implementations
│   ├── Interpolator.cs / InterpolatorOutput.cs
│   ├── Interpolators/              ← Type-specific interpolators
│   ├── Transition.cs / TransitionScheduler.cs
│   ├── TransitionEffect.cs
│   ├── State.cs
│   ├── ThemeValueConverters.cs
│   └── UIThreadInspector.cs
└── GlobalUsings.cs
```
