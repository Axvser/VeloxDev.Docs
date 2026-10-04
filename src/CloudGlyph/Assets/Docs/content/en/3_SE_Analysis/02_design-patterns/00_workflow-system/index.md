# Design Patterns — Workflow System

Design-pattern analysis for the workflow-system feature (editor VM layer + the CompilerEx compile/run engine). The pages below analyze each pattern the feature employs, with Mermaid class diagrams and code excerpts sourced from the current repository.

| Page | Content |
|---|---|
| [Class Diagram](00_class-diagram/index.md) | Mermaid class diagrams (overview over three pages) |
| [Patterns Overview](01_patterns-overview/index.md) | Pattern → location table |
| [Template Method](02_template-method/index.md) | Helper lifecycle skeleton (`Install`/`Uninstall`/`CloseAsync`) + overridable hooks |
| [Command Pattern](03_command-pattern/index.md) | `WorkflowActionPair` undo/redo command stack |
| [Observer Pattern](04_observer-pattern/index.md) | Helper collection events, `PropertyChanged` observation, and `IExecutionObserver` |
| [Strategy Pattern](05_strategy-pattern/index.md) | `ICompileTimeRouter` Static/Dynamic branch selection |
| [Proxy / Decorator](06_proxy-decorator/index.md) | Source-generated partial VMs forwarding to Helpers |
| [Facade](07_facade/index.md) | `WorkflowBuilder` attribute types |
| [Composition](08_composition/index.md) | Nodes own slots; links derived as node pairs |
| [Virtual Proxy](09_virtual-proxy/index.md) | Spatial virtualization of `VisibleItems` |
| [Strategy (runtime)](10_strategy-runtime/index.md) | `IRedirectable` whole-graph re-run toward a predecessor Order |
| [Strategy Family (Host Capabilities)](11_host-capabilities/index.md) | The 2026-09-27 host seams as a Strategy family, with Null Object as every default |
| [Memento (Checkpoints)](12_checkpoint-memento/index.md) | `ExecutionCheckpoint` as Memento: snapshot boundary, `Rekey` guard, resume refusal |

Inside `00_class-diagram` the three diagrams are on [Class Diagram: Core / Execution Model](00_class-diagram/00_core-model/index.md), [Component Model](00_class-diagram/01_component-model/index.md) and [Class Diagram of the Runtime Capability Layer](00_class-diagram/02_runtime-capabilities/index.md).
