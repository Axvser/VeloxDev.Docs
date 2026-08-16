# 工作流系统 — 快速入门

## 工作流系统 — 快速入门

VeloxDev 工作流系统是一个跨平台的视觉化工作流编辑引擎。你可以用四类组件 —— **Tree（树）**、**Node（节点）**、**Slot（槽位）**、**Link（连接线）** —— 构建图；用 `[WorkflowBuilder.*]` 属性修饰 partial ViewModel，Roslyn 源生成器会生成完整的 ViewModel：属性、命令、Helper 装配、撤销/重做以及序列化管道。可选的 AI 层（`VeloxDev.Core.Extension`）让大语言模型通过约 60 个工具驱动编辑器，并可连接 MCP 服务器。

### 1. 安装 / 添加依赖

添加核心包：

```bash
dotnet add package VeloxDev.Core            # WorkflowSystem 核心
dotnet add package VeloxDev.Core.Extension  # Agent / MCP 工具包（可选）
```

再为你的 UI 框架添加适配器：

```bash
dotnet add package VeloxDev.WPF
```

| 框架 | 适配器包 |
|---|---|
| WPF | `VeloxDev.WPF` |
| Avalonia | `VeloxDev.Avalonia` |

WPF 演示在 `WorkflowView.xaml`（第 7 行）从 `VeloxDev.WPF` 程序集引用 `VeloxDev.WorkflowSystem.AttachedBehaviors`。WinUI / MAUI 适配器在仓库中存在，但以同样的 `VeloxDev.*` 命名约定发布属于*推断*（未从演示源码验证）。

### 2. 定义组件

每个组件都是一个以 `[WorkflowBuilder.*]` 属性修饰的 `partial` 类，其类型参数是该组件的 Helper。`[VeloxProperty]` 把字段变成可通知属性；`[AgentContext(language, "text")]` 为 AI 代理描述成员。

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`，第 11-20 行

```csharp
[AgentContext(AgentLanguages.Chinese, "派生的Tree组件之一")]
[AgentContext(AgentLanguages.English, "The workflow tree (canvas). Contains all nodes, slots, and connections. This is the root scope the Agent operates on.")]
[WorkflowBuilder.Tree<AgentHelper>]
public partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();

    [VeloxProperty] private ObservableCollection<string> executionLog = [];
    [VeloxProperty] private bool isWorkflowRunning = false;
}
```

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/NodeViewModel.cs`，第 9-24 行

```csharp
[AgentContext(AgentLanguages.Chinese, "派生的Node组件之一，作为任务执行者，默认大小为 320*260 ")]
[WorkflowBuilder.Node
    <HttpHelper<NodeViewModel>>
    (workSemaphore: 5)]
public partial class NodeViewModel : ICompileTimeAware, IRuntimeAware
{
    public NodeViewModel() => InitializeWorkflow();

    [AgentContext(AgentLanguages.Chinese, "输入口")]
    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [AgentContext(AgentLanguages.Chinese, "输出口")]
    [VeloxProperty] public partial SlotViewModel OutputSlot { get; set; }
}
```

`workSemaphore: 5` 是该节点 `ReceiveCommand` 的并发容量。Slot 和 Link 更简单：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/SlotViewModel.cs`，第 6-13 行；`LinkViewModel.cs`，第 7-14 行

```csharp
[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class LinkViewModel
{
    public LinkViewModel() => InitializeWorkflow();

    [AgentContext(AgentLanguages.Chinese, "True表示使用折线连接两个节点")]
    [VeloxProperty] private bool usePolyline = true;
}
```

### 3. 构建图

创建 Tree，设置画布原点尺寸，然后用 `tree.GetHelper()` 创建节点并连接槽位。演示会话正是这样做的：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`，第 20-38、88-108、111-165、200-216 行

```csharp
var tree = new TreeViewModel();
tree.Layout.OriginSize = new Size(3200, 2200);
var helper = tree.GetHelper();
var nodeSize = new Size(300, 260);

NodeViewModel CreateNode(string title, int delayMilliseconds, double left, double top, int priority = 0)
    => new()
    {
        Title = title,
        DelayMilliseconds = delayMilliseconds,
        Size = nodeSize,
        Anchor = new Anchor(left, top, 0),
    };

var loadSeed = CreateNode("Load Seed", 900, 340, 120, priority: 1);

foreach (var node in new IWorkflowNodeViewModel[] { controller, loadSeed, /* ... */ })
{
    helper.CreateNode(node);
}

// Slots
loadSeed.InputSlot = CreateInputSlot();                          // SlotChannel.OneSource
loadSeed.OutputSlot = CreateOutputSlot(SlotChannel.MultipleTargets);

// Connections
Connect(tree, controller.OutputSlot!, loadSeed.InputSlot!);

private static SlotViewModel CreateInputSlot(SlotChannel channel = SlotChannel.OneSource)
    => new() { Channel = channel };

private static SlotViewModel CreateOutputSlot(SlotChannel channel)
    => new() { Channel = channel };

private static void Connect(IWorkflowTreeViewModel tree, IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)
{
    tree.GetHelper().SendConnection(sender);
    tree.GetHelper().ReceiveConnection(receiver);
}
```

连接协议是：`SendConnection(sender)` 标记发送方并显示虚拟连接，`ReceiveConnection(receiver)` 进行校验（`SlotChannel` 容量 + `ValidateConnection`）并通过 `tree.GetHelper().CreateLink(...)` 创建 `Link`。

### 4. 撤销 / 重做

树上每个变更操作都会作为 `WorkflowActionPair(redo, undo)` 提交并压入并发撤销栈。把按钮绑定到生成的命令：

> 源码：`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml`，第 130-131 行

```xml
<Button Content="Undo" Width="100" Height="50" Command="{Binding UndoCommand}" />
<Button Content="Redo" Width="100" Height="50" Margin="0,8,0,0" Command="{Binding RedoCommand}" />
```

`UndoCommand` 弹出操作对并执行其 `Undo`，随后压入重做栈；`RedoCommand` 相反。节点创建、连接创建、槽位创建、`SlotEnumerator` 选择器切换和节点删除都可撤销 —— 见 `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs` 第 181-227 行的 `StandardSubmit` / `StandardUndo` / `StandardRedo`。

### 5. 编译与执行

`CompilerViewModel.CompileAsync(起点)` 把从起点可达的子图分解成若干无环编译图；`CompilerEngine.RunAsync(graph, context, ct)` 驱动图执行。演示控制器以自身为起点，先编译、再运行（需要 `using VeloxDev.Core.WorkflowSystem.CompilerEx;`）：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`，第 29-58 行

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

public CompilerViewModel Compiler { get; } = new();

[VeloxCommand]
private async Task Compile(object? parameters, CancellationToken ct)
{
    await Compiler.CompileAsync(this);          // 以自身为起点分解编译图
    OnPropertyChanged(nameof(HasCompiledGraphs));
}

[VeloxCommand]
private async Task Run(object? parameters, CancellationToken ct)
{
    var graph = Compiler.Graphs.FirstOrDefault();
    if (graph is null) return;

    var context = new RuntimeContext { IsRunning = true };  // 运行会话（日志/共享变量/进度）
    RuntimeContext = context;
    OnPropertyChanged(nameof(RuntimeContext));

    _runCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
    try
    {
        await new CompilerEngine().RunAsync(graph, context, _runCts.Token);
    }
    finally
    {
        _runCts.Dispose();
        _runCts = null;
    }
}
```

`CompileAsync` 返回 `IReadOnlyList<CompiledGraph>`；线性段编译为 `ExecuteEntry`，分支节点编译为 `BranchEntry`（`ICompileTimeRouter`），扇出为 `ParallelEntry`。`RunAsync` 逐个驱动条目，把 `RuntimeContext` 注入每个 `IRuntimeAware` 节点、经 `ReceiveAsync` 执行并链式传递返回值。分支节点实现 `ICompileTimeRouter`（静态/动态两种模式）：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/BoolSelectorNodeViewModel.cs`，第 92-118 行

```csharp
[WorkflowBuilder.Node<BoolSelectorHelper>(workSemaphore: 1)]
public partial class BoolSelectorNodeViewModel : ICompileTimeRouter, ICompileTimeAware
{
    public BoolSelectorNodeViewModel()
    {
        InitializeWorkflow();
        OutputSlots.SetSelector(typeof(bool));
    }

    [VeloxProperty]
    [SlotSelectors(typeof(bool))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    // Static → 返回当前选中值（编译期可定）；Dynamic → 编译期(null)返回 null（IsDynamic），运行期再解析
    public Task<object?> ResolveRouteKey(object? payload)
    {
        if (CompileMode == RouterCompileMode.Dynamic && payload is null)
            return Task.FromResult<object?>(null);
        return Task.FromResult<object?>(Condition);
    }

    public Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()
    {
        var dict = new Dictionary<object, List<IWorkflowNodeViewModel>>();
        if (CompileMode == RouterCompileMode.Static)
            AddBranch(dict, Condition, Condition ? TrueSlot : FalseSlot);
        else
        {
            AddBranch(dict, true, TrueSlot);
            AddBranch(dict, false, FalseSlot);
        }
        return Task.FromResult<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>>(
            dict.ToDictionary(kv => kv.Key, kv => (IReadOnlyList<IWorkflowNodeViewModel>)kv.Value.AsReadOnly()));
    }
}
```

`SetSelector(typeof(bool))` 构建两个条件输出槽（`true` / `false`）；`GetRouteTable` 登记各分支的下游（无下游的分支登记为终端分支），`ResolveRouteKey` 返回当前应走的分支 key —— 静态模式编译期锁定、剪枝未选中分支；动态模式运行期重解析。节点在 `ReceiveAsync` 中调用 `RuntimeContext.Error()/Warn()` 或抛异常即请求重定向：实现 `IRedirectable` 则按返回的 Order 重跑整张图（可跨链），否则流程结束、状态 `-1`。

### 6. 序列化

`VeloxDev.MVVM.Serialization.ComponentModelEx` 通过 Newtonsoft 将整个图（节点、槽位、连接、布局、自定义 `[VeloxProperty]` 数据）序列化为 JSON。保存与加载使用 `Serialize<T>()` / `Deserialize<T>()` 并重跑布局：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`，第 174-182 行；`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`，第 46-51 行

```csharp
using VeloxDev.MVVM.Serialization;

[VeloxCommand]
private async Task Save(object? parameter)
{
    if (parameter is not string path) return;
    await Helper.CloseAsync();
    var json = this.Serialize();
    using var writer = new StreamWriter(path, append: false);
    await writer.WriteAsync(json).ConfigureAwait(false);
}

// 加载时：
var result = json.Deserialize<TreeViewModel>();
result.Layout.UpdateCommand.Execute(null);
```

`CanvasLayout.AdaptTo(Size)` 为新原点尺寸重算实际画布尺寸并建议视口中心（`Src/Core/VeloxDev.Core/WorkflowSystem/CanvasLayout.cs`，第 21-44 行）；`Layout.UpdateCommand` 重新应用它。

### 7. 让 AI 控制工作流

`tree.AsAgentScope()` 打开流式的 `WorkflowAgentScope`。配置发现、安全级别、语言与回调，然后生成渐进式系统提示词和工具列表，交给 `chatClient.AsAIAgent(...)`：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`，第 83-141 行

```csharp
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)   // 默认提示词语言
    .WithOutputLanguage(AgentLanguages.Chinese)   // 默认输出语言
    .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithMaxToolCalls(200)
    .WithToolCallCallback(args => { helper.ToolCalled?.Invoke(); return Task.CompletedTask; })
    .WithSelectionHandler(async args => { if (helper.SelectionHandler is not null) await helper.SelectionHandler(args); })
    .WithConfirmationHandler(async args => { if (helper.ConfirmationHandler is not null) await helper.ConfirmationHandler(args); });

scope.WithInteractionSafety(helper.InteractionSafety);   // 0~3

var contextPrompt = scope.ProvideProgressiveContextPrompt();
var tools = scope.ProvideTools();

var agent = chatClient.AsAIAgent(instructions: contextPrompt, tools: tools);
```

然后用 `agent.RunAsync(message, session)` 执行一轮对话：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`，第 26-61 行

```csharp
var response = await helper.Agent.RunAsync(message, helper.Session);
var text = response.Text;
```

MCP 服务器可以加载并合并进工具集：

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`，第 53-91 行；`McpServerConfiguration.cs`，第 5-36 行

```csharp
var mcp = new McpScope().WithMcpRoot(".evn/mcp");
var mcpTools = await mcp.LoadAsync([
    new McpServerConfiguration
    {
        Name = "Email",
        RunMode = McpServerRunMode.Dotnet,
        Package = "sharp-email-mcp/SharpEmailMcp.dll",
    },
]);
```

注意属性名是 `Package` 而不是 `NpmPackage` —— 对于 `Dotnet` 模式它是 `.evn/mcp/dotnet/` 下的 DLL 路径。

### 8. 验证

- 运行 WPF 演示（`Examples/Workflow/WPF/Demo`）：它打开一个 15 节点的成品图，支持撤销/重做/保存/加载、1000 节点性能测试以及 Agent 对话面板（`WorkflowView.xaml.cs`，`InitializeNetworkDemo`）。
- `WorkflowSystem` 测试项目覆盖值类型（`AnchorTests`、`SizeTests`、`ViewportTests`、`OffsetTests`、`CellKeyTests`、`CanvasLayoutTests`）、空间索引（`SpatialGridHashMapTests`）、选择器（`SlotEnumeratorTests`）、操作对（`WorkflowActionPairTests`、`WorkflowHistoryTests`）与树操作（`WorkflowTreeExTests`）——见 `Src/Core/VeloxDev.Core.Test/WorkflowSystem`；编译器语义（`CompilerExTests`、`ParallelFanOutTests`、`RedirectTests`、`TerminalBranchTests`）在 `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions`。

### 9. 完整代码

一个组合上述各部分的最小端到端示例：

```csharp
using VeloxDev.AI;
using VeloxDev.Core.WorkflowSystem.CompilerEx;
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
        await compiler.CompileAsync(a);                       // 以节点 a 为起点分解编译图
        var graph = compiler.Graphs.FirstOrDefault();
        if (graph is not null)
            await new CompilerEngine().RunAsync(graph,
                new RuntimeContext { Data = "seed" }, CancellationToken.None);

        var json = tree.Serialize();
        var copy = json.Deserialize<MyTree>();
        copy.Layout.UpdateCommand.Execute(null);
    }
}
```
