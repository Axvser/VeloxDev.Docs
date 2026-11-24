# Canvas Input and Navigation

Core turns native pointer and key input into one routed, cancellable vocabulary, and exposes the scroll/navigation capabilities an attached surface can register. This section catalogues that public surface plus the shared hit-test geometry and the four WPF attached behaviors that translate platform input into the route.

All types are in `VeloxDev.WorkflowSystem` unless a page says otherwise. `WorkflowNavigationEx` lives in `VeloxDev.WorkflowSystem.StandardEx`; the adapter behaviors live in `VeloxDev.WorkflowSystem.AttachedBehaviors`.

## Pages

- [Input routing](00_input-routing/index.md) — `WorkflowInput`, `InputRelay`, `WorkflowEventHandle`, the pointer and key event arguments, and the three input enums.
- [Surface navigation](01_surface-navigation/index.md) — the scroller and navigator contracts, `SurfaceScrollerCore`, the wheel profile, and `Locate()`.
- [Hit testing and geometry](02_hit-testing-geometry/index.md) — `LinkCurve`, `ILinkHitTestable`, `LinkHitTestEx`, and `SlotHitTestEx`.
- [Surface math](03_surface-math/index.md) — `WorkflowSurfaceMath`, `WorkflowBounds`, `SurfaceMetrics`, `SurfaceAvailableArea`, and the metrics push helpers.
- [Viewport state](04_viewport-state/index.md) — `SurfaceViewport`, `SurfaceViewportFeed`, and `SurfaceViewportRestoreCore`.
- [Adapter behaviors](05_adapter-behaviors/index.md) — the WPF surface, transform, node-drag, and slot-connection attached properties.

## Layer split

| Layer | Types | Responsibility |
|---|---|---|
| Core | `WorkflowInput`, `IInputEvents`, `InputRelay`, event arguments, enums, `WorkflowEventHandle` | The route, the shared handle, the platform-neutral argument shape. |
| Core | `IWorkflowSurfaceScroller`, `IWorkflowSurfaceNavigator`, `SurfaceScrollerCore`, `SurfaceWheelProfile` | Wheel-to-scroll and canvas-point-to-centre arithmetic. |
| Core | `LinkCurve`, `LinkHitTestEx`, `SlotHitTestEx`, `WorkflowSurfaceMath` | Geometry shared by every adapter. |
| Adapter (WPF shown) | `WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior` | Named-part resolution, native gesture translation, per-view drag and connection. |

## Related

- [Canvas Input and Navigation Quick Start](../../1_QuickStart/07_canvas-input-navigation/index.md) shows the same types in a runnable host.
- [Platform Adapter Contract](../../1_QuickStart/24_platform-adapter-contract/index.md) explains the named parts every adapter resolves.
