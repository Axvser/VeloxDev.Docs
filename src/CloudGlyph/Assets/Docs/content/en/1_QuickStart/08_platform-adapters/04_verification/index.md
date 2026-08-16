# Platform Adapters — Verification

Build and run the app. The workflow view renders; nodes drag when their header is dragged; slots connect on press/release; the minimap tracks the viewport and navigates when dragged; the grid decorator follows the pan. For WPF, run the demo at `Examples/Workflow/WPF/Demo` and compare the "节点总数" (total nodes) counter against the "可见组件数" (visible items) counter — the latter should stay small regardless of total node count, confirming virtualization.
