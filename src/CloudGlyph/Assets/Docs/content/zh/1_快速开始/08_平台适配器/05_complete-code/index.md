# 平台适配器 — Complete Code

下面是一份自洽、可编译的 WPF 工程（net9.0-windows，引用 `VeloxDev.WPF`）。它把模板生成的文件（`wpf-v-tree`、`wpf-v-node`、`wpf-v-slot`、`wpf-v-link`、`wpf-v-selector`、`wpf-v-minimap`）与一份精简但完整的 `GridDecorator`、`LinkView` 组合在一起（模板会生成带标尺/箭头的更丰富版本；此处保持相同公开形状，保证每个符号都有定义）。把 `DataContext` 绑定到一个由 `[WorkflowBuilder.Tree]` 生成器产生的 `IWorkflowTreeViewModel`。

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

- ⚠️ 未实际运行 — 仅静态验证。（GUI 演示无法在此环境中运行。）上面的代码由模板生成文件与 WPF 演示（`Examples/Workflow/WPF/Demo/Views/Workflow/`）拼装而成，针对文档化的 API 面可编译，但尚未在此实际执行。
