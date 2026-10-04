# 复杂度分析 —— 工作流代理

## `WithAutoDiscovery` 程序集扫描

`WithAutoDiscovery` 跑两趟。第 1 趟枚举目标程序集中的每个类型（$T$ 个），每个类型做常数时间的工作（抽象/接口检查、`IWorkflow*ViewModel` 可赋值性、特性存在性）。第 2 趟深扫每个*已注册*组件：对含 $P$ 个属性、$F$ 个字段、$M$ 个方法的组件，每个成员被归入 enum/interface/data 桶，并以 `HashSet` 守卫去重（`_globallyDiscoveredTypes`），故重访为常数时间。

$$
T_{\text{discovery}} = O\!\left(T + \sum_{C \in \text{registered}} (P_C + F_C + M_C) \cdot k\right)
$$

其中 $k$ 为泛型参数递归因子（受最大泛型嵌套深度约束）。注册桶是 `HashSet`，故 `TryRegister*` 期望 $O(1)$。空间为已注册类型集：

$$
S_{\text{discovery}} = O(R_{\text{comp}} + R_{\text{enum}} + R_{\text{iface}} + R_{\text{data}})
$$

*来源：`WorkflowAgentScope.cs` `WithAutoDiscovery`。*

## `WorkflowStateTracker.TakeSnapshot` / 差异

`BuildSnapshot` 遍历整图：$V$ 个节点与 $E$ 条可见链接。对每个节点反射其公开实例属性（`AppendScalarProps`，每节点 $P$ 个）并产出 JSON 树：

$$
T_{\text{snapshot}} = O(V \cdot P + E), \qquad S_{\text{snapshot}} = O(V \cdot P + E)
$$

`ComputeDiff` 为节点与链接构建 `RuntimeId → JObject` 字典，$O(V + E)$，然后对每个节点经 `JToken.DeepEquals` 比较标量/枚举属性：

$$
T_{\text{diff}} = O(V + E + V \cdot P') = O(V \cdot P' + E)
$$

其中 $P' \le P$ 是 JSON 中的标量属性数。只捕获标量与枚举类型属性，故差异绝不物化完整子树比较。

*来源：`WorkflowStateTracker.cs` `BuildSnapshot`、`ComputeDiff`、`IndexById`。*

## 工具包派发

每个工具被 `TrackedAIFunction` 包装，其开销每次调用 $O(1)$（互锁计数器 + 事件触发 + 可选 `MarkDirty`）。预检闸门 `CheckBudget` 为 $O(1)$：一次 `IsToolEnabled` 哈希集探查、一次可选的到根账本的上行、三次整数比较。工具函数体主导：

$$
T_{\text{tool}} = O(\text{per-tool work}), \qquad T_{\text{tracked}} = T_{\text{tool}} + O(1)
$$

### 逐工具复杂度

| 工具 | 时间 | 依据 |
|---|---|---|
| `ListNodes` / `FindNodes` | $O(V \cdot P)$ | 一趟遍历节点，每节点标量属性 |
| `GetNodeDetail` / `GetNodeDetailById` | $O(P + S)$ | 单节点，$S$ 个槽（按 id 增加 $O(V)$ 的 id 扫描） |
| `GetFullTopology` | $O(V \cdot (P + S) + E)$ | 整图 |
| `ListConnections` / `ListSlotProperties` | $O(L)$ / $O(V \cdot P + S)$ | 链接 / 节点+属性 |
| `GetWorkflowSummary` | $O(V)$ | 不同类型名一趟 |
| `SearchForward` / `SearchReverse` / `SearchAllRelative` / `IsConnected` / `FindPath` | $O(V + E)$ | 带 visited/parent 的 BFS |
| `CreateNode` | $O(V)$ 期望，有空间图时 $O(1)$ | 重叠扫描 |
| `MoveNode` / `SetNodePosition` / `ResizeNode` / `DeleteNode` / `DeleteSlot` | $O(1)$ | 一次命令派发 + 等待 |
| `ConnectSlots` / `ConnectSlotsById` / `ConnectByProperty` | 摊还 $O(1)$ | 槽解析 + Send/Receive 命令 + `VerifyConnection` |
| `PatchNodeProperties` / `PatchComponentById` | $O(P)$ | 反射补丁，逐属性拒绝规则 |
| `RunCompiledWorkflow` / `GetNodeResult` | 编译 + 链/锥工作 | 见下 |
| `ListCreatableTypes` | $O(A \cdot T)$ | 程序集扫描 |
| `ValidateWorkflow` | $O(V + E)$ | 节点/链接一趟，含重复链接去重 |
| `RequestSelection` / `RequestConfirmation` | $O(1)$ + 处理器 | 用户等待主导 |
| `TakeSnapshot` / `GetChangesSinceSnapshot` | $O(V \cdot P + E)$ | 见上 |

*来源：`WorkflowAgentToolkit.cs` 各工具函数体；`TrackedAIFunction.cs`；`QueryToolNames`。*

## 编译运行 / 终结点结果

两个链入口共用 `RunCompiledRoleAsync`（`WorkflowAgentToolkit.cs`）。编译步骤从树构建编译图；Root 运行随后驱动整条可达链，而 Terminal 运行只驱动被查询节点的祖先锥（其编译与运行成本随锥而非整树伸缩）：

$$
T_{\text{Root}} = O\big(V + E\big)_{\text{compile}} + O(\text{chain work}), \qquad
T_{\text{Terminal}} = O\big(V_{\text{cone}} + E_{\text{cone}}\big)_{\text{compile}} + O(\text{cone work})
$$

引擎维护一个运行时会话（`RuntimeContext`）：运行记账（`Status`、`Attempt`、`Outcome`、`Logs`）每个被驱动步 $O(1)$，日志为 $O(\text{steps})$。前向一致的 Terminal 契约 —— 路由器选中兄弟分支意味着 `TargetReached = false` 并显式报 `error` 且**无**伪造取值 —— 运行后检查为 $O(1)$。

## 运行句柄家族

句柄注册表是一个受单锁保护的 `Dictionary<string, CompiledRun>`；句柄分配为 `Interlocked.Increment`。每次调用：

- `StartCompiledWorkflow` / `ContinueCompiledWorkflow`：一次编译（同上）+ 一次字典写入 —— 由编译主导的 $O(V+E)$。
- `GetCompiledRunStatus`：`SnapshotLogs()` 在日志锁下为 $O(\log)$（复制留存列表），随后取尾部 $\min(40, L)$ 行；注册表读取/移除期望 $O(1)$。日志尾内存由 `RunStatusLogTail = 40` 约束。

$$
T_{\text{status}} = O(\min(40, L)) + O(1), \qquad S_{\text{tail}} = O(40)
$$

- `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`：$O(1)$ —— 翻一个门标志或 `CancellationTokenSource.Cancel`。

`ContinueCompiledWorkflow` 增加一次检查点加载，$O(\text{checkpoint size})$。

## `ToolCallLedger` 链

`Spend` 递归到 `Outer`，因此一次调用的成本即账本链深度：

$$
T_{\text{spend}} = O(d), \qquad S_{\text{ledger}} = O(d)
$$

其中 $d$ 是派发深度（受子代理深度上限约束）。`ResetChain` 同为 $O(d)$。`Usage` 是三次无锁 `Volatile.Read`，$O(1)$。

## `WorkflowAgentContextProvider` 渲染缓存

`BuildContext` 先读 `Scope.ContextKey`（$O(1)$：一次 `Version` 读加一次预算档计算）并与已发布键比较。命中时它不加锁、不分配，返回上一个 `AIContext`。未命中时重建指令，且（仅当 `Version` 移动时）重建工具列表：

$$
T_{\text{render}} = \begin{cases} O(1) & \text{缓存命中} \\ O(\text{instructions} + n_{\text{tools}}) & \text{缓存未命中} \end{cases}
$$

能力包络测试直接测量未命中成本：包络比静态骨架小一个数量级，且 1000 次空闲轮分配 **0 字节**。

## `McpScope.LoadAsync`

`LoadAsync` 遍历 $N$ 个服务器配置；每服务器的成本是安装（本地模式）+ 连接：

$$
T_{\text{load}}(N) = \sum_{i=1}^{N} \left( T_{\text{install}}(i) + T_{\text{connect}}(i) \right)
$$

**npm/pip 安装幂等。** `EnsureNpmPackageAsync` 以 `"node:{package}@{version}"`（pip：`"py:..."`）为键存于进程级列表，由全局 `SemaphoreSlim(1,1)` 保护。首次安装后记忆化检查为 $O(1)$：

$$
T_{\text{install}} = \begin{cases} O(\text{npm/pip work}) & \text{首次} \\ O(1) & \text{已记忆} \end{cases}
$$

**传输 + 握手。** `ConnectServerAsync` 执行 JSON-RPC `initialize`/`tools/list` 握手；成本由进程启动与工具列表主导，$O(\text{spawn} + \text{handshake} + \text{toolSchemaSize})$。逐服务器失败成本 $O(1)$，不中断整批。

## 汇总

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `WithAutoDiscovery(assembly)` | $O(T + R \cdot m \cdot k)$ | $O(R)$ 集 | $T$ 类型，$R$ 已注册，$m$ 成员/组件，$k$ 泛型递归 |
| `WorkflowStateTracker.TakeSnapshot` | $O(V \cdot P + E)$ | $O(V \cdot P + E)$ | 图遍历 + 标量反射 |
| `WorkflowStateTracker` 差异 | $O(V \cdot P' + E)$ | $O(V + E)$ | `RuntimeId` 索引 + 属性 `DeepEquals` |
| 工具包派发开销 | $O(1)$ | $O(1)$ | 包装器计数 + 事件 |
| `CheckBudget` 闸门 | $O(1)$（+ 到根 $O(d)$） | $O(1)$ | 哈希探查 + 整数比较 |
| `ToolCallLedger.Spend` / `ResetChain` | $O(d)$ | $O(d)$ | 沿派发链上行 |
| 提供器渲染 | 命中 $O(1)$ / 未命中 $O(\text{text} + n_{\text{tools}})$ | 命中 $O(1)$ | `ContextKey` 缓存 |
| `GetCompiledRunStatus` | $O(\min(40, L))$ | $O(40)$ | `SnapshotLogs()` + 尾部 |
| `StartCompiledWorkflow` | $O(V + E)$ 编译 + $O(1)$ | $O(V + E)$ | 编译主导 |
| `Pause` / `Resume` / `StopCompiledRun` | $O(1)$ | $O(1)$ | 门标志 / 令牌取消 |
| `McpScope.LoadAsync` | $O(N \cdot (T_{\text{install}} + T_{\text{connect}}))$ | $O(\text{tools})$ | 首次加载后安装记忆化 $O(1)$ |
