# Workflow compiler

`CompilerViewModel` turns the graph reachable from one node into a `CompiledGraph`: an ordered list of `ChainSegment`, `BranchSegment` and `ParallelSegment` objects. The compiled graph describes every possible execution and fixes each node's compile order; it does not run anything.

Two roles decide the direction of the walk:

- `CompileRole.Root` compiles the subgraph reachable downstream from a start node.
- `CompileRole.Terminal` walks upstream and compiles only the ancestor cone needed to compute one node.

The pages below build each role against a real graph:

- [Root compilation](00_root-compilation/index.md) — chains, fan-out, joins, compile order and the flat outline.
- [Branches and terminal compilation](01_branches-and-terminal/index.md) — routers, static pruning, parallel segments and reverse compilation.

The compiler lives in `VeloxDev.Core.WorkflowSystem.CompilerEx`, inside `VeloxDev.Core`. No package beyond the graph-model prerequisites is needed.
