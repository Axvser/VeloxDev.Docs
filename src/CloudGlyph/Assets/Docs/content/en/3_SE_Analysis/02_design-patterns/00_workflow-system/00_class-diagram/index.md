# Workflow System — Design Patterns — Class Diagram

Mermaid class diagrams for the workflow-system feature. Each diagram is on its own page so this page stays an overview.

| Page | Diagram |
|---|---|
| [Class Diagram: Core / Execution Model](00_core-model/index.md) | Diagram A — the CompilerEx compile→run machinery and the context hierarchy that flows through every node |
| [Component Model](01_component-model/index.md) | Diagram B — the component model: VM interfaces, their helpers, the topology they expose |
| [Class Diagram of the Runtime Capability Layer](02_runtime-capabilities/index.md) | The 2026-09-27 host-capability layer: the seven seams, their implementations, and why they hang off the concrete `RuntimeContext` rather than off the contract |

For the adapter/attached-behaviors side (per-platform surfaces that host this VM tree: drag, connect, view-pool virtualization, minimap) see the `08_platform-adapters` feature's class-diagram page.
