# Software Engineering Analysis

This section analyzes the VeloxDev architecture across five fixed dimensions. Every dimension is further divided by **feature** (Workflow System, Transition System, Dynamic Theme, MVVM, AOP + MonoBehaviour + WeakTypes), matching the feature inventory established during discovery.

```mermaid
flowchart LR
    A[SE Analysis] --> B[0 · File Structure]
    A --> C[1 · Feature Map]
    A --> D[2 · Design Patterns]
    A --> E[3 · Data Flow]
    A --> F[4 · Complexity]
    C --> C0[Workflow System]
    C --> C1[Transition System]
    C --> C2[Dynamic Theme]
    C --> C3[MVVM]
    C --> C4[AOP + MonoBehaviour + WeakTypes]
    D --> D0[Workflow System]
    D --> D1[Transition System]
    D --> D2[Dynamic Theme]
    D --> D3[MVVM]
    D --> D4[AOP + MonoBehaviour + WeakTypes]
    E --> E0[Workflow System]
    E --> E1[Transition System]
    E --> E2[Dynamic Theme]
    E --> E3[MVVM]
    E --> E4[AOP + MonoBehaviour + WeakTypes]
    F --> F0[Workflow System]
    F --> F1[Transition System]
    F --> F2[Dynamic Theme]
    F --> F3[MVVM]
    F --> F4[AOP + MonoBehaviour + WeakTypes]
```

| Dimension | Description |
|---|---|
| [File Structure](0_file_structure) | Repository layout, project-to-folder mapping, Mermaid flowchart |
| [Feature Map](1_feature_map) | Module responsibility boundaries, feature → project → dependency mapping |
| [Design Patterns](2_design_patterns) | Patterns used by each feature (Command, Template Method, Proxy, Registry, ...) |
| [Data Flow](3_data_flow) | PlantUML sequence diagrams for each feature's core API call chains |
| [Complexity](4_complexity) | KaTeX time/space complexity for each feature's core operations |

## Feature Index

| Feature | Owning Project | Evidence |
|---|---|---|
| Workflow System (+ Agent / AI / MCP) | `VeloxDev.Core` + `VeloxDev.Core.Extension` | Demo (`Examples/Workflow`) + Test |
| Transition System | `VeloxDev.Core` + adapters | Demo (`Examples/Transition`, 6 platforms) + Test |
| Dynamic Theme | `VeloxDev.Core` + adapters | Demo (`Examples/Theme`) + Test |
| MVVM | `VeloxDev.Core` + `VeloxDev.Core.Generator` | Demo (`Examples/MVVM`) + Test |
| AOP + MonoBehaviour + WeakTypes | `VeloxDev.Core` | Demo (`Examples/AOP`, `Examples/MonoBehaviour`) + Test |
