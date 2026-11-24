# Canvas input and navigation

`WorkflowInput` routes pointer and keyboard events to a tree's components. An adapter translates its platform's input into the standard arguments and calls `Route`; Core decides who hears about it, and the host decides what to do. Navigation and hit testing are the two other operations built on the same model data.

- [Input routing](00_input-routing/index.md) — `WorkflowInput.Route`, bubbling, `WorkflowEventHandle` and the adapter boundary.
- [Surface navigation](01_surface-navigation/index.md) — `Locate`, scroller arithmetic, slot and link hit testing.

```csharp
var input = WorkflowInput.For(tree);
input.Route(new PointerMovedEventArgs(anchor, modifiers, source, target, handle));
```

Namespace: `VeloxDev.WorkflowSystem`.
