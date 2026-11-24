# Platform adapter contract

The contract lives in `VeloxDev.Core`, namespace `VeloxDev.WorkflowSystem`. It is the surface every GUI adapter closes: one input route, a scroll/navigation capability pair, the metrics and overlay data exchange, the view-pool composition, and the model-event sinks. None of these types mentions a platform; an adapter supplies the platform half.

| Role | Contract types | Who implements it |
| --- | --- | --- |
| Input route | `WorkflowInput`, `IInputEvents`, `InputRelay` | Core owns the route; an adapter translates native input into the standard arguments |
| Scroll and navigation | `IWorkflowSurfaceScroller`, `IWorkflowSurfaceNavigator` | The adapter registers one on `WorkflowInput` while its surface is attached |
| Surface metrics | `SurfaceMetrics`, `SurfaceViewport`, `SurfaceCanvas`, `SurfaceViewportRestoreCore` | Core computes; the adapter reads its scroll container |
| Grid and minimap | `IWorkflowGridDecorator`, `IWorkflowMinimapOverlay` | Core declares; the host or adapter implements |
| View pool | `ViewPool`, `ViewPoolCore`, `ViewSourcePipelineCore`, `IViewPoolPolicy` | Core owns the pool; each adapter closes the generic composition |
| Model events | `INodeEventSink`, `ISlotEventSink`, `ITreeEventSink` | Core declares; an adapter attaches a sink through markup |
| Conformance | `VeloxDev.AdapterTestKit.TestGraph` | The shared fixture every headless suite drives |

## Pages

- [WorkflowInput and the input relay](00_workflow-input/index.md) — the one route per tree, the per-helper relay, and the event handle.
- [Input event arguments](01_event-arguments/index.md) — the pointer and keyboard argument types an adapter constructs.
- [Input enumerations](02_input-enums/index.md) — `InputKey`, `InputModifiers` and `MouseButton`.
- [Scroll and navigation](03_scroll-and-navigation/index.md) — the two capabilities, the platform host contract, and `SurfaceScrollerCore`.
- [Surface metrics](04_surface-metrics/index.md) — the immutable snapshots and the push helpers.
- [Viewport restore](05_viewport-restore/index.md) — the save/restore state machine and the host it drives.
- [Surface math](06_surface-math/index.md) — the coordinate conversions every adapter shares.
- [Overlay contracts](07_overlay-contracts/index.md) — `IWorkflowGridDecorator` and `IWorkflowMinimapOverlay`.
- [View pool](08_view-pool/index.md) — the pool engine, its policy and the serializable tuning profile.
- [View hosting layers](09_view-hosting-layers/index.md) — the nine small contracts the pool composes.
- [Event sinks](10_event-sinks/index.md) — the model-event counterpart to routed input.
- [Conformance kit](11_conformance-kit/index.md) — the shared `TestGraph` fixture.

A minimal contract call needs no GUI:

```csharp
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
tree.SetHelper(new TreeHelper(200d));

var input = WorkflowInput.For(tree);      // one instance per tree
input.Scroller?.ScrollBy(0d, -120d);      // null until an adapter registers one
```

**Expected result:** `WorkflowInput.For(tree)` returns the same object on every call, and `Scroller` is `null` until a surface attaches.
