# Transition animation

A transition is declared as a chain of segments. `Execute` validates the chain, creates a run on the target's scheduler, and lets the interpreter sample one frame at a time until the last segment ends.

The analysis splits into two operations:

- [Execute chain](00_execute-chain/index.md) — declaration, validation, run registration, segment replay and control-plane calls.
- [Sampling and scheduling](01_sampling-and-scheduling/index.md) — the interpreter loop, easing and frame application, cancellation and resources.

```csharp
transition.Property(t => t.Opacity, 0d, 1d).AwaitThen(TimeSpan.FromMilliseconds(250));
transition.Execute(target);
```

Namespace: `VeloxDev.TransitionSystem`.
