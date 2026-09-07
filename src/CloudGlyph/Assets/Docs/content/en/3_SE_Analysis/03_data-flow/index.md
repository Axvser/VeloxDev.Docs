# 03 · Data Flow

PlantUML sequence diagrams for each feature's core API call chains. Each page covers the normal flow, the error/exception paths, and async/event-driven scenarios where applicable.

| Feature | Core flows |
|---|---|
| [00 Workflow System](00_workflow-system) | Connect → compile (Root) → run segments → reverse/Terminal cone compile & run → redirect re-run → broadcast dispatch |
| [01 Workflow Agent](01_workflow-agent) | Tool call → component command → undo/diff; interaction confirmation; compiled Root run & Terminal result (not-reached error); MCP server load |
| [02 MVVM](02_mvvm) | Command enqueue → start → complete/cancel/fail → exit |
| [03 Transition](03_transition) | Execute chain → per-target scheduler (mutual/non-mutual) → Prepare → FPS-paced sampling loop → UI-thread apply → lifecycle events |
| [04 Dynamic Theme](04_dynamic-theme) | `InitializeTheme` registration + converter pipeline → animated/instant switch (`Transition`/`Jump`) → runtime overrides (`SetThemeValue`/`RestoreThemeValue`) |
| [05 AOP](05_aop) | CreateProxy → set hooks → invoke → start/coverage/end chain |
| [06 MonoBehaviour](06_monobehaviour) | Start channel → update/late/fixed ticks → stop |
| [07 Weak Types](07_weak-types) | Enqueue/push → sweep-on-access → dequeue/pop |
| [08 Platform Adapters](08_platform-adapters) | Attach & wiring → pan/pointer → zoom collapse → node drag → slot connect → minimap navigation |
