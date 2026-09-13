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

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`，第 14-15 行（`[WorkflowBuilder.Tree<AgentHelper>]`）。

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

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` 的 `Compile` 命令（`await Compiler.CompileAsync(this, CompileRole.Root);`，约第 33 行）。

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

**示例：** `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 的 `Save` 命令（约第 252 行 `var json = this.Serialize();`）；`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs` 的 `SelectWorkflow`（约第 65 行 `json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`）。

**说明：** 设置包含 `TypeNameHandling.Auto`、`PreserveReferencesHandling.Objects`、`WritablePropertiesOnlyResolver`。
