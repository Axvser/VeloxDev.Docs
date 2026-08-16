# 01 · 功能结构

## 功能 → 项目 → 依赖

Wiki 围绕**功能**而非目录组织。功能是项目对外暴露的一组内聚能力——可独立描述、使用和验证。下表是跨「快速开始、API、SE 分析」三个维度使用的权威映射。

| 功能 | 所属项目 | 公共 API 面（摘要） | 依赖 | 证据 |
|---|---|---|---|---|
| **工作流系统** | `VeloxDev.Core`（序列化来自 `VeloxDev.Core.Extension`） | `[WorkflowBuilder.*]`、`IWorkflowTreeViewModel` 家族、`CompilerEx`、`SelectorEx`、`StandardEx`、`SpatialGridHashMap` | Roslyn 生成器 | Demo + Test |
| **工作流代理** | `VeloxDev.Core.Extension` | `WorkflowAgentScope`、`WorkflowAgentToolkit`（约 60 个工具）、`McpScope`、`VeloxDev.AI` | `Microsoft.Extensions.AI`、`ModelContextProtocol` | Test + README + Demo |
| **MVVM** | `VeloxDev.Core` | `VeloxPropertyAttribute`、`VeloxCommandAttribute`、`VeloxCommand`、`IVeloxCommand` | Roslyn 生成器 | Demo + Test |
| **过渡动画** | `VeloxDev.Core` + 适配器 | `Eases`、`Transition<T>`、`InterpolatorCore`、`TransitionSchedulerCore`、原生插值器 | `System.Numerics`、`System.Drawing` | Demo + Test |
| **动态主题** | `VeloxDev.Core` + 适配器 | `ThemeManager`、`ThemeConfigAttribute`、`IThemeObject`、转换器 | 过渡引擎 | Demo + Test |
| **AOP** | `VeloxDev.Core`（`#if NET`） | `ProxyEx`、`ProxyInstance`、`AopCache`、`IAspectOriented` | `DispatchProxy`、生成器 | Demo + Test |
| **MonoBehaviour** | `VeloxDev.Core` | `MonoBehaviourManager`、`MonoBehaviourAttribute`、`IMonoBehaviour` | Roslyn 生成器 | Demo + Test |
| **弱引用类型** | `VeloxDev.Core` | `WeakDelegate`、`WeakQueue`、`WeakStack`、`WeakCache` | — | Test |
| **平台适配器** | 6 个适配器 + `Src/Templates` | 附加工作流行为、各平台过渡/主题接线、`dotnet new` 模板 | 各框架 SDK | README + Demo + 源码 |

## 模块职责边界

```mermaid
flowchart TD
    subgraph Core [VeloxDev.Core]
        WF[WorkflowSystem<br/>图模型 · 撤销重做 · 空间索引 · 编译器]
        MV[MVVM<br/>可观察属性 · 异步命令]
        TR[TransitionSystem<br/>插值 · 缓动 · 调度器]
        TH[DynamicTheme<br/>主题注册 · 切换]
        AOP[AspectOriented<br/>代理拦截]
        MB[MonoBehaviour<br/>帧循环]
        WT[WeakTypes<br/>弱集合]
        AI[AI<br/>代理属性 + 反射]
    end
    subgraph Ext [VeloxDev.Core.Extension]
        AGT[工作流代理<br/>约 60 个工具 · 状态跟踪]
        MCP[MCP 作用域<br/>stdio 服务器]
        SER[ComponentModelEx<br/>JSON 序列化]
    end
    subgraph Adapters [VeloxDev.WPF / Avalonia / WinUI / MAUI / WinForms / Razor]
        AB[附加工作流行为<br/>表面 · 拖拽 · 连接 · 池 · 小地图]
        PA[PlatformAdapters<br/>插值器 · 主题转换器 · UI 线程]
    end
    GEN[VeloxDev.Core.Generator<br/>源生成器] --> WF
    GEN --> MV
    GEN --> TH
    GEN --> AOP
    GEN --> MB
    EXT --> Core
    AGT --> AI
    Adapters --> Core
    PA --> TR
    PA --> TH
```

## 入口点

| 场景 | 入口类型 | 位置 |
|---|---|---|
| 构建工作流编辑器 | `tree.AsAgentScope()` / `[WorkflowBuilder.Tree<T>]` | `Examples/Workflow/Common/Lib` |
| 为属性做动画 | `target.Snapshot(...)` / `Transition.Execute(...)` | `Examples/Transition/*` |
| 切换主题 | `ThemeManager.Transition<Light>(...)` | `Examples/Theme/*` |
| 运行异步命令 | 分部方法上的 `[VeloxCommand]` | `Examples/MVVM/*` |
| 拦截节点执行 | `ProxyEx.CreateProxy(...)` + `SetProxy(...)` | `Examples/AOP/*` |
| 基于 tick 的模拟 | `[MonoBehaviour]` + `MonoBehaviourManager.Start()` | `Examples/MonoBehaviour/*` |
| 安装预制视图 | `dotnet new wpf-v-node -n NodeView ...` | `Src/Templates` |
