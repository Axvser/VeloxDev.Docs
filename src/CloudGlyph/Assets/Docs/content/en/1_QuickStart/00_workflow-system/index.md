# Workflow System — Quick Start

## Workflow System

VeloxDev WorkflowSystem is a cross-platform visual workflow editing and execution engine. You build a graph from four kinds of components — **Tree**, **Node**, **Slot**, **Link** — by decorating partial ViewModels with `[WorkflowBuilder.*]` attributes; a Roslyn source generator emits the full ViewModel (properties, commands, helper wiring, undo/redo, connection plumbing). The engine core is UI-framework-agnostic; per-platform *adapters* supply the rendering behaviors and belong to the separate `08_platform-adapters` feature.

The engine executes a graph three ways, and this Quick Start walks all three:

1. **Node level** — drive one node's `ReceiveCommand`, which forwards a `TaskContext` into `Helper.ReceiveAsync`.
2. **Edge level** — a node broadcasts a payload along its links (`StandardBroadcastAsync`); every accepted edge delivers a `TaskContext` to the downstream node.
3. **Chain level (compiled)** — `CompilerViewModel.CompileAsync(node, role)` decomposes a reachable sub-graph into one acyclic `CompiledGraph`, and `RuntimeEngine.RunAsync(graph, RuntimeContext)` drives it. The role tells the compiler *what the node means*: `CompileRole.Root` (the node starts a forward run) or `CompileRole.Terminal` (the node is the result you want — the compiler reverse-compiles its ancestor cone).

This feature's pages assume the `.NET`/C# console project you create in `01_install`. No GUI is required: compiling and running the graph happens headless in the core engine.

## Quick Start — Sub-pages

This feature's Quick Start is split into the following pages:

- [00 Prerequisites](00_prerequisites/) — supported target frameworks, SDK, repository layout
- [01 Install & Create the Project](01_install/) — create the console project and add the `VeloxDev.Core` (+ `VeloxDev.Core.Extension` for serialization) dependencies
- [02 Define the Components](02_define-components/) — declare the Tree / Slot / Link / Node classes and their custom `NodeHelper<T>` execution logic
- [03 Build the Graph](03_build-a-graph/) — instantiate the canvas, register nodes, set slot channels, and connect them
- [04 Compile & Run Forward](04_compile-and-run/) — compile forward with `CompileRole.Root` and run with `RuntimeEngine`
- [05 Compile a Result (Terminal)](05_terminal-compile/) — reverse-compile a result with `CompileRole.Terminal` (ancestor cone, `Target` / `TargetReached`)
- [06 Serialize & Rebuild the Tree](06_serialization/) — serialize the whole tree to JSON (`VeloxDev.MVVM.Serialization.ComponentModelEx`) and rebuild it
- [07 Verify & Complete Code](07_complete-code/) — verification against tests & demos, the single-file runnable program, and the run declaration
