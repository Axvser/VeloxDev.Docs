# 工作流系统 — 快速开始

## 工作流系统

### 快速开始

VeloxDev 工作流系统是一个跨平台的视觉化工作流编辑引擎。你可以用四类组件 —— **Tree（树）**、**Node（节点）**、**Slot（槽位）**、**Link（连接线）** —— 构建图；用 `[WorkflowBuilder.*]` 属性修饰 partial ViewModel，Roslyn 源生成器会生成完整的 ViewModel：属性、命令、Helper 装配、撤销/重做以及序列化管道。引擎与 UI 框架无关；适配器（WPF / Avalonia）提供渲染行为。可选的 AI 层（`VeloxDev.Core.Extension`）让大语言模型通过约 60 个工具驱动编辑器 —— 那是独立的*工作流代理*功能（`01_工作流代理`），此处不展开。

#### 1. 前置条件

- **支持目标**（来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` —— 可用于 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+。
- **SDK / 运行时：** 带 Roslyn 4.x（5.0+）的 .NET SDK 以运行源码生成器；仓库内示例用 SDK 8.0+ 并面向 `net9.0` —— *被验证过*的配置，并非要求。
- **包管理器：** NuGet / `dotnet` CLI（`dotnet add package`、`dotnet restore`）。
- **必需服务：** 无 —— 核心引擎自包含。


#### 2. 安装 / 添加依赖

向控制台或库项目添加核心包：

```bash
dotnet add package VeloxDev.Core
```

若要运行 GUI 演示，请为你的 UI 框架添加适配器：

```bash
dotnet add package VeloxDev.WPF   # 或 VeloxDev.Avalonia
```

| 框架 | 适配器包 |
|---|---|
| WPF | `VeloxDev.WPF` |
| Avalonia | `VeloxDev.Avalonia` |

WPF 演示从 `VeloxDev.WPF` 程序集导入 `VeloxDev.WorkflowSystem.AttachedBehaviors`（`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml`，第 7 行）。WinUI / MAUI 适配器在仓库中存在，以同样的 `VeloxDev.*` 命名约定发布属于*推断*。

**预期结果：** 项目无错误地完成还原，`using VeloxDev.WorkflowSystem;` 可解析。

#### 3. 基础设置 / 注册

每个组件都是一个以 `[WorkflowBuilder.*]` 属性修饰的 `partial` 类，其类型参数是该组件的 Helper。`[VeloxProperty]` 把字段变成可通知属性；`[VeloxCommand]` 把方法变成 `IVeloxCommand`。源生成器生成后备成员、`InitializeWorkflow()` 与 `GetHelper()` 装配。

**Tree** —— `[WorkflowBuilder.Tree<THelper>]`：

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class MyTree
{
    public MyTree() => InitializeWorkflow();

    [VeloxProperty] private bool isWorkflowRunning = false;
}
```

**Node** —— `[WorkflowBuilder.Node<THelper>(workSemaphore: n)]`；`workSemaphore` 是该节点 `ReceiveCommand` 的并发容量：

```csharp
[WorkflowBuilder.Node<NodeHelper<MyNode>>(workSemaphore: 1)]
public partial class MyNode
{
    public MyNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}
```

**Slot** 与 **Link**：

```csharp
[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class MyLink
{
    public MyLink() => InitializeWorkflow();

    [VeloxProperty] private bool usePolyline = true;
}
```

**预期结果：** 项目可编译。每个组件都暴露 `InitializeWorkflow()`（生成）、`GetHelper()` 以及生成的命令属性（`CreateNodeCommand`、`UndoCommand`、`ReceiveCommand`、`DeleteCommand` 等）。

#### 4. 核心用法（逐步）

**1. 创建 Tree 并设置画布尺寸。**

```csharp
var tree = new MyTree();
tree.Layout.OriginSize = new Size(1200, 800);
var helper = tree.GetHelper();
```

**预期结果：** `tree.Layout.OriginSize` 为 `(1200, 800)`；`helper` 是生成的 `TreeHelper` 实例，其 `Install` 已订阅树的 `Nodes` / `Links` 集合（`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`，第 109-124 行）。

**2. 通过 helper 注册节点。**

```csharp
var a = new MyNode { Anchor = new Anchor(40, 200), Size = new Size(200, 120) };
var b = new MyNode { Anchor = new Anchor(400, 200), Size = new Size(200, 120) };
helper.CreateNode(a);
helper.CreateNode(b);
```

`helper.CreateNode(node)` 汇入 `StandardCreateNode`，提交一个可撤销的 `WorkflowActionPair` 并把节点加入 `tree.Nodes`（`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，第 27-40 行）。

**预期结果：** `tree.Nodes.Count == 2`；`a.Parent` 与 `b.Parent` 指向 `tree`。撤销栈为每次 `CreateNode` 保留一个条目。

**3. 创建槽位并配置通道。**

```csharp
a.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
a.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };
b.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
b.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };
```

`SlotChannel` 是一个 `[Flags]` 枚举：`OneSource` 最多允许 1 条入向连接，`OneTarget` 最多 1 条出向连接（`Src/Core/VeloxDev.Core/WorkflowSystem/Enums/Slot.cs`）。

**预期结果：** `a.Input.Channel == SlotChannel.OneSource`；每个槽位都注册进所属节点的 `Slots` 集合且 `Parent` 已设置。

**4. 连接槽位。**

```csharp
helper.SendConnection(a.Output);
helper.ReceiveConnection(b.Input);
```

连接协议分两阶段（`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`，第 97-171 行）：`SendConnection` 检查发送端容量、显示 `VirtualLink` 并标记 `SlotState.PreviewSender`；`ReceiveConnection` 校验容量 + `ValidateConnection`、清理同向连接冲突，然后经 `CreateLink` 建立连接，整条连接作为一个可撤销的 `WorkflowActionPair` 提交。

**预期结果：** `tree.Links.Count == 1`；`tree.LinksMap[a.Output][b.Input]` 是创建的连接；`a.Output.Targets` 包含 `b.Input`，`b.Input.Sources` 包含 `a.Output`。执行 `tree.UndoCommand.Execute(null)` 会移除连接；`tree.RedoCommand.Execute(null)` 会恢复它。

**5. 编译并运行图。**

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var compiler = new CompilerViewModel();
await compiler.CompileAsync(a);                              // 起点节点 = a
var graph = compiler.Graphs.FirstOrDefault();
if (graph is not null)
    await new CompilerEngine().RunAsync(
        graph, new RuntimeContext { Data = "seed" }, CancellationToken.None);
```

`CompileAsync` 把从 `a` 可达的子图分解成无环 `CompiledGraph`（线性段 → `ExecuteEntry`；实现 `ICompileTimeRouter` 的节点 → `BranchEntry`；路由 key 指向多个下游 → `ParallelEntry`）。`RunAsync` 逐个条目驱动，把 `RuntimeContext` 注入 `IRuntimeAware` 节点、经 `ReceiveAsync` 执行并链式传递返回值（`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`、`CompilerEngine.cs`）。

**预期结果：** 运行结束后 `graph.Entries` 非空，`context.Status` 为 `"Completed"`（取消则为 `"Stopped"`）。

**6. 序列化 / 反序列化整棵树。**

```csharp
using VeloxDev.MVVM.Serialization;

var json = tree.Serialize();
var copy = json.Deserialize<MyTree>();
copy.Layout.UpdateCommand.Execute(null);
```

`ComponentModelEx.Serialize<T>` 通过 Newtonsoft 把整个图（节点、槽位、连接、布局、自定义 `[VeloxProperty]` 数据）序列化为 JSON；`Deserialize<T>` 重建它。`CanvasLayout.UpdateCommand` 重新应用布局（`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`；`Src/Core/VeloxDev.Core/WorkflowSystem/CanvasLayout.cs`）。

**预期结果：** `copy.Nodes.Count == 2`、`LinksMap` 连接关系恢复、`copy.Layout.OriginSize == (1200, 800)`。

#### 5. 验证

- **测试：** `WorkflowSystem` 测试项目覆盖值类型（`AnchorTests`、`SizeTests`、`ViewportTests`、`OffsetTests`、`CellKeyTests`、`CanvasLayoutTests`）、空间索引（`SpatialGridHashMapTests`）、选择器（`SlotEnumeratorTests`）、操作对（`WorkflowActionPairTests`、`WorkflowHistoryTests`、`WorkflowUndoCountTests`）与树操作（`WorkflowTreeExTests`）——`Src/Core/VeloxDev.Core.Test/WorkflowSystem`。编译器语义（`CompilerExTests`、`ParallelFanOutTests`、`RedirectTests`、`TerminalBranchTests`）与序列化（`WorkflowSerializationTests`）在 `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions`。
- **演示：** WPF 演示（`Examples/Workflow/WPF/Demo`）打开一个多控制器的成品图，支持撤销 / 重做 / 保存 / 加载以及 1000 节点性能测试。其会话构建器使用了与上面相同的 API —— `WorkflowDemoSession.Create()`，见 `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`。

#### 6. 完整代码

一个自包含的最小端到端示例，组合了以上所有步骤。每个标识符都在下面定义或来自 `VeloxDev.*` 包。

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.MVVM.Serialization;
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class MyTree
{
    public MyTree() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper<MyNode>>(workSemaphore: 1)]
public partial class MyNode
{
    public MyNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class MyLink
{
    public MyLink() => InitializeWorkflow();
}

public static class Program
{
    public static async Task RunAsync()
    {
        var tree = new MyTree();
        tree.Layout.OriginSize = new Size(1200, 800);
        var helper = tree.GetHelper();

        var a = new MyNode { Anchor = new Anchor(40, 200), Size = new Size(200, 120) };
        var b = new MyNode { Anchor = new Anchor(400, 200), Size = new Size(200, 120) };
        helper.CreateNode(a);
        helper.CreateNode(b);

        a.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
        a.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };
        b.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
        b.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };

        helper.SendConnection(a.Output);
        helper.ReceiveConnection(b.Input);

        var compiler = new CompilerViewModel();
        await compiler.CompileAsync(a);
        var graph = compiler.Graphs.FirstOrDefault();
        if (graph is not null)
            await new CompilerEngine().RunAsync(
                graph, new RuntimeContext { Data = "seed" }, CancellationToken.None);

        var json = tree.Serialize();
        var copy = json.Deserialize<MyTree>();
        copy.Layout.UpdateCommand.Execute(null);
    }
}
```

#### 7. 运行声明

- ⚠️ 未实际运行 —— 仅静态验证。此示例依据真实源码（编译器、`StandardEx`、演示会话）编写，与 `WorkflowDemoSession.Create()` 和 `ControllerViewModel` 一致，但在文档编写期间未在控制台项目中实际编译。请将 `Program.RunAsync` 主体视为指南，在真实项目中构建后运行。
