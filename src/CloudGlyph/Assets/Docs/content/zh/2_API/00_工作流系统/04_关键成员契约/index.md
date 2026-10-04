# Workflow System — 关键成员契约

顶层 API 的条目模板形式。

### `WorkflowBuilder.TreeAttribute<T>`

**签名：**

```csharp
[WorkflowBuilder.Tree<THelper>]
public partial class TreeViewModel { public TreeViewModel() => InitializeWorkflow(); }
```

**参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `virtualLinkType` | `Type?` | 可选，覆盖虚拟连接类型（默认 `LinkDefaultViewModel`） |
| `virtualSlotType` | `Type?` | 可选，覆盖虚拟连接内部使用的槽位类型 |

**返回：** 无（属性应用于 `partial` 类；生成器发出成员）。

**异常：** 若 `THelper` 不满足 `IWorkflowTreeViewModelHelper, new()`，编译报错。

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`，第 17-18 行（`[WorkflowBuilder.Tree<AgentHelper>]`）。

**说明：** 属性的泛型参数是树的 Helper；`InitializeWorkflow()` 由生成器发出。

### `IWorkflowTreeViewModelHelper.SendConnection` / `ReceiveConnection`

**签名：**

```csharp
void SendConnection(IWorkflowSlotViewModel slot);
void ReceiveConnection(IWorkflowSlotViewModel slot);
```

**参数：** `slot` —— 发送端（或接收端）槽位，已挂载到树中的节点。

**返回：** `void`。

**异常：** 无直接异常；未挂载的槽位在 DEBUG 构建下触发 `WorkflowGuard.Fail`。

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 的 `Connect(tree, sender, receiver)` 依次调用 `tree.GetHelper().SendConnection(sender)` 与 `ReceiveConnection(receiver)`。

**说明：** 两阶段协议；连接建立后整条连接作为一个可撤销的 `WorkflowActionPair` 提交。

### `CompilerViewModel.CompileAsync`

**签名：**

```csharp
Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(
    T component, CompileRole role, CancellationToken ct = default)
    where T : IWorkflowViewModel;
```

**参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `component` | `T : IWorkflowViewModel` | 必须是 `IWorkflowNodeViewModel`；按 `role` 扮演起点或终端 |
| `role` | `CompileRole` | `Root` = 沿下游 `Targets` 分解起点可达子图；`Terminal` = 沿 `Sources` 反向编译目标节点的祖先锥 |
| `ct` | `CancellationToken` | 可选取消令牌 |

**返回：** `IReadOnlyList<CompiledGraph>` —— 当前实现恒返回一张编译图；同时清空并重填 `Graphs`。

**异常：** 若 `component` 不是 `IWorkflowNodeViewModel`，抛 `ArgumentException`；`role` 越界抛 `ArgumentOutOfRangeException`；`Terminal` 锥不可表达（前驱不汇聚、多条路由分支到达目标）抛 `InvalidOperationException`。

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` 的 `Compile` 命令（`await Compiler.CompileAsync(this, CompileRole.Root);`，第 52 行）。

**说明：** 线性段 → `ChainSegment`、路由点 → `BranchSegment`、单键/普通节点多目标扇出 → `ParallelSegment`；编译完给每个 `ICompileTimeAware` 节点注入 `CompileContext`（`Order`/`ChainIndex`/`Offset`，未选中分支 `Order = -1`）。

### `ComponentModelEx.Serialize` / `Deserialize`

**签名：**

```csharp
string Serialize<T>(this T workflow) where T : INotifyPropertyChanged;
T Deserialize<T>(this string json) where T : INotifyPropertyChanged;
```

**参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `workflow` | `T : INotifyPropertyChanged` | 任意工作流树 ViewModel |
| `json` | `string` | `Serialize`（或 options 变体）产生的 JSON |

**返回：** `Serialize` → JSON 字符串；`Deserialize` → 新的 `T` 实例。

**异常：** `Serialize` 对 null workflow 抛 `ArgumentNullException`；`Deserialize` 对 null / 空 JSON 抛 `ArgumentException`，结果为空时抛 `JsonSerializationException`。`TryDeserialize` 返回 `false` 而非抛出。

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 的 `Save` 命令（第 291 行 `var json = this.Serialize();`）；`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs` 的 `SelectWorkflow`（第 71、73 行 `json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`）。

**说明：** 设置包含 `TypeNameHandling.Auto`、`PreserveReferencesHandling.Objects`、`WritablePropertiesOnlyResolver`。

## `RuntimeEngine.RunAsync`

**签名：**

```csharp
Task RunAsync(
    CompiledGraph graph,
    IRuntimeContext context,
    CancellationToken ct,
    ExecutionCheckpoint? resumeFrom = null);
```

**参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `graph` | `CompiledGraph` | 要驱动的编译图。为 `null` 时立即返回。 |
| `context` | `IRuntimeContext` | 运行会话。为 `null` 时立即返回。 |
| `ct` | `CancellationToken` | 取消会在下一个节点边界停下整轮；`OperationCanceledException` 被吸收成 `Status = "Stopped"`。 |
| `resumeFrom` | `ExecutionCheckpoint?` | 可选，从哪份检查点继续 —— 通常就是 `RuntimeContext.CheckpointStore` 里那份。全新一轮就省略它（或传 `null`）。 |

**返回：** `Task` —— 运行结束时完成。之后读 `Status`、`Outcome`、`Data`、`TargetReached`、`Attempt`。

**异常：** `resumeFrom` 取自另一张图（在碰会话之前拒绝；`Status` 停在 `"Idle"`），或重定向超过 50 次时抛 `InvalidOperationException`。

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` 的 Run/Resume 驱动：

```csharp
var context = new RuntimeContext { IsRunning = true, Data = SeedPayload };
ConfigureSessionWith(context);              // 宿主策略：门、观察者、重试、接收器、补偿、存储、日志写入器
ExecutionCheckpoint? place = resume ? await CheckpointSource(ct) : null;
await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);
```

**说明：** 引擎自己负责下游派发 —— 编译运行期间节点从不广播。`Attempt` 数的是过图趟数（`1 + 重定向次数`），重试不推进它。

## `RuntimeContext` 的宿主能力属性

**签名：** `public sealed partial class RuntimeContext : IRuntimeContext`

九个可选属性，全部默认「关」，因此在都不设置时，运行的表现与它们存在之前一模一样。完整说明见`运行时上下文`。

| 属性 | 类型 | 效果 |
|---|---|---|
| `ExecutionGate` | `IExecutionGate?` | 每个节点前等待一次；门关着时 `Status` 为 `"Paused"`。 |
| `Observer` | `IExecutionObserver?` | 接收运行时间线。 |
| `RetryPolicy` | `INodeRetryPolicy?` | 决定抛出异常的节点能不能再来一次。 |
| `ErrorSink` | `IExecutionErrorSink?` | 把失败作为记录收到。 |
| `Compensation` | `IExecutionCompensation?` | 得知失败/取消运行的成果，最近的在前。 |
| `CheckpointStore` | `IExecutionCheckpointStore?` | 每个节点成功后把运行位置写到哪里。 |
| `LogWriter` | `ILogWriter?` | 运行的行去哪（除 `Logs` 之外）。 |
| `MaxRetainedLogs` | `int?` | 限制内存中的 `Logs`。`0` 表示一行不留。 |
| `MaxParallelBranches` | `int?` | 限制一次扇出同时有多少分支在跑。`null` = 不限；`1` = 串行。 |

**示例（Demo）：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 的 `ConfigureRun(RuntimeContext context)` —— 在同一个会话上设置全部七个能力对象。

**说明：** 它们刻意**不**是 `IRuntimeContext` 的成员：加一个会破坏每个外部实现，而它们是宿主策略而非会话状态。引擎经私有助手转型到 `RuntimeContext` 来读，该助手同时会拆开扇出的 `BranchRuntimeContext`，因此它们在并行组内部依然有效。自带 `IRuntimeContext` 实现的宿主得到的是不限流、无观察的行为。

## `ExecutionCheckpoint` + 恢复

**签名：**

```csharp
public sealed class ExecutionCheckpoint
{
    public int Attempt { get; set; }
    public int? ActiveRedirectTarget { get; set; }
    public object? Data { get; set; }
    public Dictionary<string, object?> Outputs { get; set; }
    public List<string> Shape { get; set; }
    public List<string> Types { get; set; }

    public static ExecutionCheckpoint Rekey(ExecutionCheckpoint checkpoint, CompiledGraph target);
}
```

**参数（`Rekey`）：** `checkpoint` —— 写下的那份位置；`target` —— 要适配到的那张图（同结构、不同节点身份，也就是序列化往返产生的东西）。

**返回：** 一份以 `target` 身份归档的新检查点；输入保持不动。

**异常：** 检查点为 `null` 时抛 `ArgumentNullException`；两张图不是同一结构（节点数不同，或某位置节点类型不同）时抛 `InvalidOperationException`。

**示例（已实测）：**

```csharp
var store = new InMemoryCheckpointStore();
var context = new RuntimeContext { CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, context, ct, null);      // 中途停下
var saved = await store.LoadAsync(CancellationToken.None);

var resumed = new RuntimeContext();
await new RuntimeEngine().RunAsync(graph, resumed, CancellationToken.None, saved);
// resumed.Status == "Completed"；检查点记录为完成的节点没有被再次驱动。
```

**说明：** 检查点按 `RuntimeId` 归档，所以经过序列化的图全是新 id，对它恢复会被**拒绝**而不是猜 —— 这是刻意的，`Rekey` 是显式说「两张图同结构」的入口。检查点把 `IGroupData` 存成按节点键归档的普通 `Dictionary<string, object?>`，因为节点引用写不下来（而且会顺带把整棵树拖进去）。
