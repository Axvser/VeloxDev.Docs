# 04 · Complexity

Time and space complexity analysis of each feature's core operations, using KaTeX for formulas. Each page covers construction, execution, look-up, serialization, and memory usage.

| Feature | Representative bounds |
|---|---|
| [00 Workflow System](00_workflow-system) | Spatial hash query, compile (Root/Terminal), segment execution, undo/redo, selector lookup, serialize |
| [01 Workflow Agent](01_workflow-agent) | Auto-discovery scan, JSON snapshot diff, tool dispatch, Root/Terminal compile + run |
| [02 MVVM](02_mvvm) | Command queueing (semaphore), property notifications |
| [03 Transition](03_transition) | Property-path parse, sampler prepare, per-frame interpolation, scheduler fan-out, snapshot discovery |
| [04 Dynamic Theme](04_dynamic-theme) | Theme lookup, per-instance active cache |
| [05 AOP](05_aop) | Proxy invocation dispatch, `AopCache` resolution |
| [06 MonoBehaviour](06_monobehaviour) | Behavior dispatch per frame, fixed-update interval |
| [07 Weak Types](07_weak-types) | Sweep-on-access, adaptive cleanup threshold |
| [08 Platform Adapters](08_platform-adapters) | View pool reuse, spatial virtualization, zoom collapse, minimap projection |
