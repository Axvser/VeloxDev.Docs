# JavaScript module

File: `wwwroot/veloxdev.workflow.js`, shipped inside `VeloxDev.Razor` and served as `_content/VeloxDev.Razor/veloxdev.workflow.js`.

The components import the module on demand. Every export forwards to the same-named function on `window.veloxdevWorkflow`, so a host can call one without importing the module first. The wheel initializers install non-passive `wheel` listeners, and the zoom path dispatches `veloxdev-wf-layout-changed` on the frame after a zoom; a hand-written zoom path must dispatch that event or slot anchors stay at their pre-zoom positions.

## Surface and viewport

| Export | Parameters | Result |
| --- | --- | --- |
| `initSurface` | `scrollerEl, canvasHostEl, dotnetRef, initialW, initialH, contentX, contentY, initialOffsetX, initialOffsetY, initialScrollX, initialScrollY` | Handle with `dispose()`; starts scroll reporting and DOM edge extension. |
| `getCanvasTranslate` | `canvasEl` | `{ x, y }` translate of the canvas. |
| `toCanvasLocal` | `scrollerId, clientX, clientY` | `[x, y]` canvas-local point. |
| `getViewportSize` | `scrollerEl` | `{ width, height }` of the scroll viewport. |
| `scrollToRatio` | `scrollerId, ratioX, ratioY` | Scrolls to a fraction of the scroll range. |
| `scrollToPosition` | `scrollerId, x, y` | Scrolls to absolute offsets. |
| `scrollByDelta` | `scrollerId, dx, dy` | Adds a pixel delta. |
| `scrollSurfaceBy` | `scrollerId, dx, dy` | Wheel-style scroll used by the surface scroller. |
| `setSurfaceLayout` | `scrollerId, contentX, contentY` | Publishes the content translate for the grid/axis layers. |
| `ensureCanvasSize` | `scrollerId, width, height` | Grows the canvas host to at least the requested size. |
| `applySurfaceNavigation` | `scrollerId, layoutX, layoutY, contentW, contentH, scrollX, scrollY` | Applies translate, extent and scroll in one synchronous step. |
| `applyZoomSurface` | `scrollerId, layoutX, layoutY, contentW, contentH, scrollX, scrollY, nodeGeometry` | Applies the whole zoom transaction in one browser frame. |

## Grid and minimap

| Export | Parameters | Result |
| --- | --- | --- |
| `measureMinimapArea` | `scrollerId` | `{ availableRight, availableTop, availableBottom, overlayWidth }`. |
| `setMinimapMapping` | `scrollerId, scale, ox, oy, minX, minY, maxX, maxY` | Stores the content-fit mapping. |
| `setMinimapViewport` | `scrollerId, worldX, worldY, vw, vh` | Moves the viewport block. |
| `refreshMinimapViewport` | `scrollerId` | Re-applies the last world rect after a re-render. |
| `initMinimap` | `minimapEl, scrollerId, dotnetRef` | Handle with `dispose()`; enables drag navigation. |

## Per-view gestures

| Export | Parameters | Result |
| --- | --- | --- |
| `initNodeDrag` | `nodeEl, dotnetRef` | Handle; calls `OnNodeDrag` / `OnNodeDragEnd` and `RequestPressVerdict`. |
| `setNodePosition` | `nodeEl, x, y` | Repositions a node wrapper without a .NET render. |
| `initSlotConnection` | `slotEl, dotnetRef` | Handle; performs the rubber-band gesture and reports start/move/end. |
| `initSlotLayout` | `hostEl, dotnetRef` | Handle; measures `data-slot-id` elements and posts `[id, x, y]` batches. |
| `initWheelZoom` | `scrollerEl, dotnetRef` | Handle; coalesces Ctrl+wheel notches into one `OnWheelZoom` call. |
| `initWheelScroll` | `scrollerEl, dotnetRef` | Handle; `preventDefault`s the plain wheel synchronously and routes it. |

## Interop contract

- The .NET side is `WorkflowSurfaceBehavior`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior` and `WorkflowMinimapOverlay`.
- Coordinate batches and geometry arrays are stringified with `.` decimals; a comma-decimal culture must not parse them.
- Disposing a handle cancels every listener and observer that handle installed.
