# Workflow System — Quick Start

## Workflow System — Quick Start

VeloxDev WorkflowSystem is a cross-platform visual workflow editing engine. You build a graph from four kinds of components — **Tree**, **Node**, **Slot**, **Link** — decorate partial ViewModels with `[WorkflowBuilder.*]` attributes, and the Roslyn source generator emits the full ViewModel: properties, commands, helper wiring, undo/redo and serialization plumbing. An optional AI layer (`VeloxDev.Core.Extension`) lets an LLM drive the editor through a toolkit of about 60 tools and can connect to MCP servers.

### 1. Install / Add Dependency

Add the core packages:

```bash
dotnet add package VeloxDev.Core            # WorkflowSystem core
dotnet add package VeloxDev.Core.Extension  # Agent / MCP toolkit (optional)
```

Then add the adapter for your UI framework:

```bash
dotnet add package VeloxDev.WPF
```

| Framework | Adapter package |
|---|---|
| WPF | `VeloxDev.WPF` |
| Avalonia | `VeloxDev.Avalonia` |

The WPF demo references `VeloxDev.WorkflowSystem.AttachedBehaviors` from the `VeloxDev.WPF` assembly (`WorkflowView.xaml`, line 7). WinUI / MAUI adapters exist in the repository but are *inferred* to ship under the same `VeloxDev.*` naming convention (not verified against demo source).

### 2. Define Components

Each component is a `partial` class annotated with a `[WorkflowBuilder.*]` attribute whose type parameter is the component's Helper. `[VeloxProperty]` turns a field into a change-notifying property; `[AgentContext(language, "text")]` documents the member for the AI agent.

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, lines 11-20

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

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/NodeViewModel.cs`, lines 9-24

```csharp
[AgentContext(AgentLanguages.Chinese, "派生的Node组件之一，作为任务执行者，默认大小为 320*260 ")]
[WorkflowBuilder.Node
    <HttpHelper<NodeViewModel>>
    (workSemaphore: 5)]
public partial class NodeViewModel : ICompileTimePriority
{
    public NodeViewModel() => InitializeWorkflow();

    [AgentContext(AgentLanguages.Chinese, "输入口")]
    [VeloxProperty] public partial SlotViewModel InputSlot { get; set; }

    [AgentContext(AgentLanguages.Chinese, "输出口")]
    [VeloxProperty] public partial SlotViewModel OutputSlot { get; set; }
}
```

`workSemaphore: 5` is the concurrency capacity of the node's `WorkCommand`. Slots and links are even simpler:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/SlotViewModel.cs`, lines 6-13 and `LinkViewModel.cs`, lines 7-14

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

### 3. Build a Graph

Create a tree, set the canvas origin size, then use `tree.GetHelper()` to create nodes and connect slots. The demo session does exactly this:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, lines 20-38, 88-108, 111-165, 200-216

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
        CompilePriority = priority,
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

The connection protocol is: `SendConnection(sender)` marks the sender and shows the virtual link, `ReceiveConnection(receiver)` validates (`SlotChannel` capacity + `ValidateConnection`) and creates a `Link` via `tree.GetHelper().CreateLink(...)`.

### 4. Undo / Redo

Every mutating operation on the tree is submitted as a `WorkflowActionPair(redo, undo)` and pushed onto a concurrent undo stack. Bind buttons to the generated commands:

> Source: `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml`, lines 130-131

```xml
<Button Content="Undo" Width="100" Height="50" Command="{Binding UndoCommand}" />
<Button Content="Redo" Width="100" Height="50" Margin="0,8,0,0" Command="{Binding RedoCommand}" />
```

`UndoCommand` pops the pair and runs its `Undo` action, then pushes it onto the redo stack; `RedoCommand` does the inverse. Connection creation, node creation, slot creation, `SlotEnumerator` selector switches and node deletes are all undoable — see `StandardSubmit` / `StandardUndo` / `StandardRedo` in `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, lines 181-227.

### 5. Compile & Execute

The `WorkflowCompiler` turns the graph into an ordered execution plan. The demo controller compiles from itself with the four dimension settings and then runs the chain:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`, lines 61-85

```csharp
[VeloxCommand]
private async Task OpenWorkflow(object? parameters, CancellationToken ct)
{
    var tree = Parent as TreeViewModel;
    tree?.BeginWorkflowRun();
    try
    {
        var compiler = new WorkflowCompiler();
        var context = NetworkFlowContext.Create(SeedPayload);
        var results = compiler.Compile(this, CompileMode, CompileDirection, CompileScope, CycleHandling);
        if (results.Count == 0) return;
        var result = results[0];
        await result.ExecuteAsync(context, ct);
    }
    catch
    {
        tree?.EndWorkflowRun();
        throw;
    }
}
```

`Compile(startNode, mode, direction, scope, cycleHandling)` returns `IReadOnlyList<CompilationResult>`; each result's `ExecuteAsync(parameter, ct)` runs its items in deterministic order and chains the parameter. Branching nodes implement `ICompileTimeRouter`:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/BoolSelectorNodeViewModel.cs`, lines 19-36, 67-91

```csharp
[WorkflowBuilder.Node<BoolSelectorHelper>(workSemaphore: 1)]
public partial class BoolSelectorNodeViewModel : ICompileTimeRouter
{
    public BoolSelectorNodeViewModel()
    {
        InitializeWorkflow();
        OutputSlots.SetSelector(typeof(bool));
    }

    [VeloxProperty]
    [SlotSelectors(typeof(bool))]
    public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public object? GetCurrentRouteKey() => Condition ? (object)true : (object)false;

    public IReadOnlyDictionary<object, IWorkflowNodeViewModel> GetRouteTable()
    {
        var dict = new Dictionary<object, IWorkflowNodeViewModel>();
        if (TrueSlot is not null)
            foreach (var target in TrueSlot.Targets)
                if (target.Parent is not null)
                    dict[true] = target.Parent;
        if (FalseSlot is not null)
            foreach (var target in FalseSlot.Targets)
                if (target.Parent is not null)
                    dict[false] = target.Parent;
        return dict;
    }
}
```

`SetSelector(typeof(bool))` builds two conditional output slots (`true` / `false`); the compiler pre-collects the route table and the executor skips branch-exclusive items of the unchosen branch.

### 6. Serialization

`VeloxDev.MVVM.Serialization.ComponentModelEx` serializes the whole graph (nodes, slots, links, layout, custom `[VeloxProperty]` data) to JSON via Newtonsoft. Save and reload use `Serialize<T>()` / `Deserialize<T>()` and then re-run layout:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, lines 174-182 and `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 46-51

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

// On load:
var result = json.Deserialize<TreeViewModel>();
result.Layout.UpdateCommand.Execute(null);
```

`CanvasLayout.AdaptTo(Size)` recomputes the actual canvas size for a new origin size and suggests a viewport center (`Src/Core/VeloxDev.Core/WorkflowSystem/CanvasLayout.cs`, lines 21-44); `Layout.UpdateCommand` re-applies it.

### 7. Let an AI control the workflow

`tree.AsAgentScope()` opens a fluent `WorkflowAgentScope`. Configure discovery, safety, language and callbacks, then produce a progressive system prompt and a tool list; hand both to `chatClient.AsAIAgent(...)`:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, lines 83-141

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

Then run a turn with `agent.RunAsync(message, session)`:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, lines 26-61

```csharp
var response = await helper.Agent.RunAsync(message, helper.Session);
var text = response.Text;
```

MCP servers can be loaded and merged into the tool set:

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/MCP/McpScope.cs`, lines 53-91 and `McpServerConfiguration.cs`, lines 5-36

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

Note the property is `Package`, not `NpmPackage` — for `Dotnet` mode it is the DLL path under the `.evn/mcp/dotnet/` root.

### 8. Verification

- Run the WPF demo (`Examples/Workflow/WPF/Demo`): it opens a ready-made 15-node graph, supports Undo/Redo/Save/Load, a 1000-node performance test, and an Agent chat pane (`WorkflowView.xaml.cs`, `InitializeNetworkDemo`).
- The `WorkflowSystem` test project covers value types (`AnchorTests`, `SizeTests`, `ViewportTests`, `OffsetTests`, `CellKeyTests`, `CanvasLayoutTests`), spatial index (`SpatialGridHashMapTests`), selector (`SlotEnumeratorTests`), action pairs (`WorkflowActionPairTests`, `WorkflowHistoryTests`) and the compiler (`WorkflowCompilerTests`, `WorkflowTreeExTests`) — see `Src/Core/VeloxDev.Core.Test/WorkflowSystem`.

### 9. Complete Code

A minimal end-to-end sample combining the pieces above:

```csharp
using VeloxDev.AI;
using VeloxDev.MVVM.Serialization;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.Compilation;

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

        var results = new WorkflowCompiler().Compile(a, CompileMode.BFS,
            CompileDirection.Forward, CompileScope.FromNode, CycleHandling.Throw);
        await results[0].ExecuteAsync("seed", CancellationToken.None);

        var json = tree.Serialize();
        var copy = json.Deserialize<MyTree>();
        copy.Layout.UpdateCommand.Execute(null);
    }
}
```
