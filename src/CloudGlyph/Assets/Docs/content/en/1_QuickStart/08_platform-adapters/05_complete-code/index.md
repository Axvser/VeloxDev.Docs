# Platform Adapters — Complete Code

The complete scaffold below is a single, self-consistent WPF project that compiles against `VeloxDev.WPF` (net9.0-windows). It combines the template-generated files (`wpf-v-tree`, `wpf-v-node`, `wpf-v-slot`, `wpf-v-link`, `wpf-v-selector`, `wpf-v-minimap`) with a minimal but complete `GridDecorator` and `LinkView` (the templates emit richer versions with rulers and arrowheads; the version below keeps the same public shape so every symbol is defined). Bind an `IWorkflowTreeViewModel` (produced by the `[WorkflowBuilder.Tree]` generator) as the `DataContext`.

Sub-pages (one per source file):

- `workflow-view/`
- `node-view/`
- `slot-view/`
- `link-view/`
- `grid-decorator/`
- `minimap-overlay/`
- `template-selector/`

---

## Run Declaration

- ⚠️ Not actually run — statically verified only. (GUI demos cannot be run in this environment.) The code above is assembled from template-generated files and the WPF demo (`Examples/Workflow/WPF/Demo/Views/Workflow/`); it compiles against the documented API surface but has not been executed here.
