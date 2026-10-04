# Workflow System — Quick Start

VeloxDev WorkflowSystem is a cross-platform visual workflow editing and execution engine. You build a graph from four kinds of components — **Tree**, **Node**, **Slot**, **Link** — by decorating partial ViewModels with `[WorkflowBuilder.*]` attributes; a Roslyn source generator emits the full ViewModel (properties, commands, helper wiring, undo/redo, connection plumbing). The engine core is UI-framework-agnostic; per-platform *adapters* supply the rendering behaviors and belong to the separate `08_platform-adapters` feature.

The engine executes a graph three ways:

1. **Node level** — drive one node's `ReceiveCommand`, which forwards a `TaskContext` into `Helper.ReceiveAsync`.
2. **Edge level** — a node broadcasts a payload along its links (`StandardBroadcastAsync`); every accepted edge delivers a `TaskContext` to the downstream node.
3. **Chain level (compiled)** — `CompilerViewModel.CompileAsync(node, role)` decomposes a reachable sub-graph into one acyclic `CompiledGraph`, and `RuntimeEngine.RunAsync(graph, RuntimeContext)` drives it. The role tells the compiler *what the node means*: `CompileRole.Root` (the node starts a forward run) or `CompileRole.Terminal` (the node is the result you want — the compiler reverse-compiles its ancestor cone).

Around the compiled run sits an optional **host-capability layer** (added 2026-09-27): a pause gate, an observer, a retry policy, an error sink, a compensator, a checkpoint store and a log writer. None of them is required — with all unset the run behaves exactly as it did before they existed — and this Quick Start walks each one.

This feature's pages assume the `.NET`/C# console project you create in [Install & Create the Project](01_install/index.md). No GUI is required: compiling and running the graph happens headless in the core engine.

## Quick Start — Sub-pages

| Page | What you do |
|---|---|
| [Prerequisites](00_prerequisites/index.md) | Supported target frameworks, SDK, repository layout |
| [Install & Create the Project](01_install/index.md) | Create the console project and add the `VeloxDev.Core` (+ `VeloxDev.Core.Extension`) references |
| [Define the Components](02_define-components/index.md) | Declare the Tree / Slot / Link / Node classes and their `NodeHelper<T>` execution logic |
| [Build the Graph](03_build-a-graph/index.md) | Instantiate the canvas, register nodes, set slot channels, connect them |
| [Compile a Graph (Root) and Run It](04_compile-and-run/index.md) | Compile forward with `CompileRole.Root` and run with `RuntimeEngine` |
| [Compile a Result (Terminal)](05_terminal-compile/index.md) | Reverse-compile a result with `CompileRole.Terminal` (`Target` / `TargetReached`) |
| [Serialize & Rebuild the Tree](06_serialization/index.md) | Serialize the whole tree to JSON and rebuild it |
| [Complete Code](07_complete-code/index.md) | The complete core program: every file, in full |
| [Pause and Resume a Run](08_pause-and-resume/index.md) | Hold a run at a node boundary with `ManualExecutionGate` |
| [Observe a Run and Read Its Outcome](09_observe-and-report/index.md) | Watch the timeline with `IExecutionObserver`; read `RunOutcome` |
| [Retry a Failing Node and Compensate a Bad Run](10_retry-and-compensate/index.md) | Retry a node that threw; hand a bad run's successes back |
| [Checkpoints and Log Files](11_checkpoint-and-logs/index.md) | Write the run's place down, resume from it, divert and cap the log |
| [Parallel Fan-Out, Its Concurrency Cap, and the Compiled Outline](12_parallel-and-outline/index.md) | Fan-out concurrency, its cap, and `CompiledOutline` |
| [Verify & Run Declaration](13_verify-and-run-declaration/index.md) | Verification against tests and demos, plus the honest run declaration |

Every page states an observable **Expected result** for each numbered step, and the pages from [Complete Code](07_complete-code/index.md) on are backed by output the author actually built and ran — see [Verify & Run Declaration](13_verify-and-run-declaration/index.md) for the recorded run.
