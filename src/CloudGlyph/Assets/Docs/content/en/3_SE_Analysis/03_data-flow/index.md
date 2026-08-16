# 03 · Data Flow

PlantUML sequence diagrams for each feature's core API call chains. Each page covers the normal flow, the error/exception paths, and async/event-driven scenarios where applicable.

| Feature | Core flows |
|---|---|
| [00 Workflow System](00_workflow-system) | Node create → connect → receive/broadcast → undo/redo → compile & run → serialize |
| [01 Workflow Agent](01_workflow-agent) | Agent tool call → mutation → state diff → confirmation; MCP stdio handshake |
| [02 MVVM](02_mvvm) | Command enqueue → start → complete/cancel/fail → exit |
| [03 Transition](03_transition) | Snapshot → schedule → interpolate frame → apply → complete |
| [04 Dynamic Theme](04_dynamic-theme) | Register → transition → interpolate themed props → theme changed |
| [05 AOP](05_aop) | CreateProxy → set hooks → invoke → start/coverage/end chain |
| [06 MonoBehaviour](06_monobehaviour) | Start channel → update/late/fixed ticks → stop |
| [07 Weak Types](07_weak-types) | Enqueue/push → sweep-on-access → dequeue/pop |
| [08 Platform Adapters](08_platform-adapters) | Attached behavior wiring → drag/connect → view pool virtualization |
