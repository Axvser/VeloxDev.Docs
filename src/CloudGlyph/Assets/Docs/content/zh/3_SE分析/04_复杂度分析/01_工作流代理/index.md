# 复杂度分析 — 工作流代理

## `WithAutoDiscovery` 程序集扫描

`WithAutoDiscovery` 分两趟运行。第一趟枚举目标程序集内的每个类型（$T$ 个类型），对每个类型做常数时间工作（抽象/接口检查、`IWorkflow*ViewModel` 可赋值性、属性存在性）。第二趟深度扫描每个*已注册*组件：对含 $P$ 个属性、$F$ 个字段、$M$ 个方法的组件，其每个成员被归入枚举/接口/数据桶，由 `HashSet` 守护去重（`_globallyDiscoveredTypes`），因此再次访问是常数时间。

对单个程序集的一次调用：

$$
T_{\text{discovery}} = O\!\left(T + \sum_{C \in \text{registered}} (P_C + F_C + M_C) \cdot k\right)
$$

其中 $k$ 是泛型参数递归因子（受最大泛型嵌套深度约束）。注册桶是 `HashSet`，故 `TryRegister*` 期望 $O(1)$。

空间即已注册类型集合：

$$
S_{\text{discovery}} = O(R_{\text{comp}} + R_{\text{enum}} + R_{\text{iface}} + R_{\text{data}})
$$

对多个程序集的重复调用会累积组件；全局 `_globallyDiscoveredTypes` 集合保证一个类型在所有语言间只被深度扫描一次。

*源码：`WorkflowAgentScope.cs`，`WithAutoDiscovery` 第 600-662 行、`ScanComponentMembers` 第 678-738 行。*

## `WorkflowStateTracker.TakeSnapshot` / 差异

`BuildSnapshot` 遍历整张图：$V$ 个节点与 $E$ 条可见连接。对每个节点反射公共实例属性（`AppendScalarProps`，每节点 $P$）并生成 JSON 树：

$$
T_{\text{snapshot}} = O(V \cdot P + E), \qquad S_{\text{snapshot}} = O(V \cdot P + E)
$$

`ComputeDiff` 以 $O(V + E)$ 为节点/连接构建 `RuntimeId → JObject` 字典，再对每个节点经 `JToken.DeepEquals` 比较标量/枚举属性：

$$
T_{\text{diff}} = O(V + E + V \cdot P') = O(V \cdot P' + E)
$$

其中 $P' \le P$ 是 JSON 中的标量属性数。只捕获标量与枚举类型属性，因此差异绝不物化整棵子树比较。

*源码：`WorkflowStateTracker.cs`，`BuildSnapshot` 第 73-124 行、`ComputeDiff` 第 126-192 行。*

## `WorkflowAgentToolkit` 工具派发

每个工具被 `TrackedAIFunction` 包装，其每次调用开销为 $O(1)$（互锁计数器 + 事件触发 + 可选 `MarkDirty`）。工具体占主导：

$$
T_{\text{tool}} = O(\text{per-tool work}), \qquad T_{\text{tracked}} = T_{\text{tool}} + O(1)
$$

### 每工具复杂度

| 工具 | 时间 | 依据 |
|---|---|---|
| `ListNodes` / `FindNodes` | $O(V \cdot P)$ | 单趟遍历节点，每节点标量属性 |
| `GetNodeDetail` / `GetNodeDetailById` | $O(P + S)$ | 单节点、$S$ 个槽（by-id 增加 $O(V)$ 的 id 扫描） |
| `GetFullTopology` | $O(V \cdot (P + S) + E)$ | 整张图 |
| `ListConnections` / `ListSlotProperties` | $O(L)$ / $O(V \cdot P + S)$ | 连接 / 节点+属性 |
| `GetWorkflowSummary` | $O(V)$ | 去重类型名单趟 |
| `SearchForward` / `SearchReverse` / `SearchAllRelative` | $O(V + E)$ | 带 visited 集合的 BFS |
| `IsConnected` | $O(V + E)$ | 正向/反向 BFS |
| `FindPath` | $O(V + E)$ | 带父映射的最短路径 BFS |
| `CreateNode` | 期望 $O(V)$，有空间地图为 $O(1)$ | 重叠扫描；空间 `QueryNodes` 为 $O(k + m)$ 单元 |
| `MoveNode` / `SetNodePosition` / `ResizeNode` / `DeleteNode` / `DeleteSlot` | $O(1)$ | 一次命令派发 + 等待 |
| `ConnectSlots` / `ConnectSlotsById` / `ConnectByProperty` | 摊还 $O(1)$ | 槽解析 + Send/Receive 命令 + `VerifyConnection` |
| `DisconnectSlots` / `DisconnectSlotsById` | $O(1)$ | `LinksMap` 查找 + 删除连接 |
| `PatchNodeProperties` / `PatchComponentById` | $O(P)$ | 反射补丁、逐属性拒绝规则 |
| `SetEnumSlotCollection` / `GetEnumSlotByValue` | $O(\text{members})$ | 选择器切换重建条目 |
| `ExecuteNode` / `ExecuteNodes` | $O(\text{node work})$ | 等待真实完成 |
| `CompileWorkflow`（Root）/ `CompileNodeResult`（Terminal） | $O(V + E)$ | `CompilerViewModel.CompileAsync(node, CompileRole{Root,Terminal})` 构建 `CompiledGraph` 条目 |
| `RunCompiledWorkflow` | $O(V + E)$ 编译 + $O(\text{chain work})$ | `CompilerViewModel.CompileAsync` + `RuntimeEngine.RunAsync` |
| `GetNodeResult` | $O(V_{\text{cone}} + E_{\text{cone}})$ 编译 + $O(\text{cone work})$ | 仅对祖先锥做 Terminal 反向编译 |
| `ListCreatableTypes` | $O(A \cdot T)$ | 扫描程序集寻找可创建节点/槽类型 |
| `ValidateWorkflow` | $O(V + E)$ | 用 `HashSet` 对重复连接去重的节点/连接趟 |
| `GetNodeStatistics` | $O(S + \text{conns})$ | 槽/目标/源遍历 |
| `RequestSelection` / `RequestConfirmation` | $O(1)$ + 处理器 | 用户等待占主导 |
| `TakeSnapshot` / `GetChangesSinceSnapshot` | $O(V \cdot P + E)$ | 见上 |

*源码：`WorkflowAgentToolkit.cs` —— 类中各处工具体；`TrackedAIFunction` 第 178-242 行；`QueryToolNames` 第 248-258 行。*

## 编译运行 / Terminal 结果

两个链入口共享 `RunCompiledRoleAsync`（`WorkflowAgentToolkit.cs`，第 1804-1861 行）。编译步骤从树构建编译图；Root 运行随后驱动整条可达链，而 Terminal 运行只驱动所查节点的祖先锥（因此其编译与运行开销随锥规模而非整棵树）：

$$T_{\text{Root}} = O\big(V + E\big)_{\text{compile}} + O(\text{chain work}), \qquad
T_{\text{Terminal}} = O\big(V_{\text{cone}} + E_{\text{cone}}\big)_{\text{compile}} + O(\text{cone work})$$

引擎维护一个运行时会话（`RuntimeContext`）：运行簿记（`Status`、`Attempt`、`Logs`）每驱动一步 $O(1)$，日志为 $O(\text{steps})$。前向一致的 Terminal 契约——路由器选中兄弟分支即 `TargetReached = false` 且显式 `error`、**不**伪造值——在运行后仅需 $O(1)$ 检查。

## `McpScope.LoadAsync`

`LoadAsync` 迭代 $N$ 个服务器配置；每个服务器的成本 = 安装（本地模式）+ 连接：

$$
T_{\text{load}}(N) = \sum_{i=1}^{N} \left( T_{\text{install}}(i) + T_{\text{connect}}(i) \right)
$$

**npm/pip 安装幂等。** `EnsureNpmPackageAsync` 以 `"node:{package}@{version}"`（pip 用 `"py:..."`）为键，存放在由全局 `SemaphoreSlim(1,1)` 守护的进程级列表中。首次安装后记忆化检查为 $O(1)$（contains）；首次安装执行一次 CLI 并记录键，因此重复加载同一包在安装上是 $O(1)$：

$$
T_{\text{install}} = \begin{cases} O(\text{npm/pip work}) & \text{首次} \\ O(1) & \text{记忆化} \end{cases}
$$

**传输 + 握手。** `ConnectServerAsync` 构建 `StdioClientTransport`（`Http` 用 `HttpClientTransport`），创建 MCP 客户端并完成 JSON-RPC `initialize`/`tools/list` 握手。成本由服务器进程启动与工具列表主导：

$$
T_{\text{connect}} = O(\text{spawn} + \text{handshake} + \text{toolSchemaSize})
$$

单服务器失败为 $O(1)$ 且不中止整批（`ServerError` 事件触发；该服务器贡献零工具）。配置了 `SynchronizationContext` 时，聚合状态维护（`McpStatusViewModel`）每次状态变更 $O(1)$ 并 marshal 到 UI 线程。

*源码：`McpScope.cs`，`LoadAsync` 第 167-191 行、`EnsureNpmPackageAsync` 第 300-332 行、`ConnectServerAsync` 第 382-418 行。*

## 汇总

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `WithAutoDiscovery(assembly)` | $O(T + R \cdot m \cdot k)$ | $O(R)$ 集合 | $T$ 类型、$R$ 注册、$m$ 成员/组件、$k$ 泛型递归 |
| `WorkflowStateTracker.TakeSnapshot` | $O(V \cdot P + E)$ | $O(V \cdot P + E)$ | 图遍历 + 标量反射 |
| `WorkflowStateTracker` 差异 | $O(V \cdot P' + E)$ | $O(V + E)$ | `RuntimeId` 索引 + 属性 `DeepEquals` |
| 工具包派发开销 | $O(1)$ | $O(1)$ | 追踪包装计数器 + 事件 |
| 查询工具（list/detail/topology） | $O(V \cdot P + E)$ | $O(\text{result})$ | 节点/槽/属性遍历 |
| 遍历（`SearchForward`、`FindPath`、`IsConnected`） | $O(V + E)$ | $O(V)$ | BFS + visited/parent |
| `CreateNode` 重叠规避 | 线性 $O(V)$，空间 $O(1)$ | $O(1)$ 暂存 | 查询单元 $k = O(1)$ 期望 |
| `SetEnumSlotCollection` | $O(\text{members})$ | $O(\text{members})$ | 选择器切换重建 |
| 编译（`CompileWorkflow`/`CompileNodeResult`） | $O(V + E)$ / $O(V_{\text{cone}} + E_{\text{cone}})$ | $O(V + E)$ | `CompilerViewModel.CompileAsync` 构建条目 |
| `RunCompiledWorkflow` | $O(V + E)$ 编译 + 链工作 | $O(V + E)$ | 编译 + `RuntimeEngine` 驱动 |
| `GetNodeResult` | $O(V_{\text{cone}} + E_{\text{cone}})$ + 锥工作 | $O(V_{\text{cone}} + E_{\text{cone}})$ | 仅 Terminal 反向编译锥 |
| `McpScope.LoadAsync` | $O(N \cdot (T_{\text{install}} + T_{\text{connect}}))$ | $O(\text{tools})$ | 首次加载后安装记忆化 $O(1)$ |
