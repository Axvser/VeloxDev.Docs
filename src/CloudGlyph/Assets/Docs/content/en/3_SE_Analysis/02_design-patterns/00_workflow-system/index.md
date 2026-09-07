# Design Patterns — Workflow System

Design-pattern analysis for the workflow-system feature (editor VM layer + the CompilerEx compile/run engine). The pages below analyze each pattern the feature employs, with Mermaid class diagrams and code excerpts sourced from the current repository.

| Page | Content |
|---|---|
| [Class diagram](00_class-diagram/index.md) | Mermaid class diagrams — core/execution model (CompilerEx) and the component VM model |
| [Patterns overview](01_patterns-overview/index.md) | Pattern → location table |
| [Template method](02_template-method/index.md) | Helper lifecycle skeleton (`Install`/`Uninstall`/`CloseAsync`) + overridable hooks |
| [Command](03_command-pattern/index.md) | `WorkflowActionPair` undo/redo command stack |
| [Observer](04_observer-pattern/index.md) | Helper collection events + `PropertyChanged` observation |
| [Strategy](05_strategy-pattern/index.md) | `ICompileTimeRouter` Static/Dynamic branch selection |
| [Proxy / Decorator](06_proxy-decorator/index.md) | Source-generated partial VMs forwarding to Helpers |
| [Facade](07_facade/index.md) | `WorkflowBuilder` attribute types |
| [Composition](08_composition/index.md) | Nodes own slots; links derived as node pairs |
| [Virtual proxy](09_virtual-proxy/index.md) | Spatial virtualization of `VisibleItems` |
| [Strategy (runtime)](10_strategy-runtime/index.md) | `IRedirectable` whole-graph re-run toward a predecessor Order |
