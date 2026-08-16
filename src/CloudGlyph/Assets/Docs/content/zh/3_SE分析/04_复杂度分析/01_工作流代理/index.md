# 复杂度分析 — 工作流代理

## `WithAutoDiscovery` 程序集扫描

`WithAutoDiscovery` 分两轮。第一轮枚举目标程序集中的每个类型（共 $T$ 个类型），每个类型做常数时间工作（抽象/接口检查、`IWorkflow*ViewModel` 可赋值性、属性存在性）。第二轮深度扫描每个*已注册*组件：一个含 $P$ 个属性、$F$ 个字段、$M$ 个方法的组件，其每个成员经 `HashSet` 守卫的去重（`_globallyDiscoveredTypes`）解析进枚举/接口/数据桶，因此重复访问为常数时间。

对单程序集的一次调用：

$$T_{\text{discovery}} = O\!\left(T + \sum_{C \in \text{registered}} (P_C + F_C + M_C) \cdot k\right)$$

其中 $k$ 是泛型参数递归因子（以最大泛型嵌套深度为界）。注册桶都是 `HashSet`，所以 `TryRegister*` 期望 $O(1)$。

空间为已注册类型集合：

$$S_{\text{discovery}} = O(R_{\text{comp}} + R_{\text{enum}} + R_{\text{iface}} + R_{\text{data}})$$

多次调用多个程序集时组件会累积；全局 `_globallyDiscoveredTypes` 集合保证一个类型在所有语言下只会被深度扫描一次。

*源码：`WorkflowAgentScope.cs` 的 `WithAutoDiscovery` 第 600-662 行、`ScanComponentMembers` 第 678-738 行。*

## `WorkflowStateTracker.TakeSnapshot` / 差异

`BuildSnapshot` 遍历整张图：$V$ 个节点与 $E$ 条可见连接。对每个节点反射公开实例属性（`AppendScalarProps`，每个节点 $P$ 个）并生成 JSON 树：

$$T_{\text{snapshot}} = O(V \cdot P + E), \qquad S_{\text{snapshot}} = O(V \cdot P + E)$$

`ComputeDiff` 为节点与连接构建 `RuntimeId → JObject` 字典，耗时 $O(V + E)$；随后对每个节点用 `JToken.DeepEquals` 比较标量/枚举属性：

$$T_{\text{diff}} = O(V + E + V \cdot P') = O(V \cdot P' + E)$$

其中 $P' \le P$ 是 JSON 中的标量属性数。只捕获标量与枚举类型属性，因此差异从不物化整棵子树比较。

*源码：`WorkflowStateTracker.cs` 的 `BuildSnapshot` 第 73-124 行、`ComputeDiff` 第 126-192 行。*

## `WorkflowAgentToolkit` 工具派发

每个工具都包在 `TrackedAIFunction` 里，其开销为每次调用 $O(1)$（interlocked 计数器 + 事件触发 + 可选 `MarkDirty`）。工具主体占主导：

$$T_{\text{tool}} = O(\text{每工具工作量}), \qquad T_{\text{tracked}} = T_{\text{tool}} + O(1)$$

### 每工具复杂度

| 工具 | 时间 | 依据 |
|---|---|---|
| `ListNodes` / `FindNodes` | $O(V \cdot P)$ | 遍历节点，每节点标量属性 |
| `GetNodeDetail` / `GetNodeDetailById` | $O(P + S)$ | 单节点，$S$ 个槽位（by-id 加一次 $O(V)$ id 扫描） |
| `GetFullTopology` | $O(V \cdot (P + S) + E)$ | 整张图 |
| `ListConnections` / `ListSlotProperties` | $O(L)$ / $O(V \cdot P + S)$ | 连接 / 节点+属性 |
| `GetWorkflowSummary` | $O(V)$ | 去重类型名扫描 |
| `SearchForward` / `SearchReverse` / `SearchAllRelative` | $O(V + E)$ | 带访问集合的 BFS |
| `IsConnected` | $O(V + E)$ | 前向/反向 BFS |
| `FindPath` | $O(V + E)$ | 带父映射的 BFS 最短路径 |
| `CreateNode` | 期望 $O(V)$，有空间映射 $O(1)$ | 重叠扫描；空间 `QueryNodes` 为 $O(k + m)$ 单元格 |
| `MoveNode` / `SetNodePosition` / `ResizeNode` / `DeleteNode` / `DeleteSlot` | $O(1)$ | 一次命令派发 + 等待 |
| `ConnectSlots` / `ConnectSlotsById` / `ConnectByProperty` | 摊还 $O(1)$ | 槽位解析 + Send/Receive 命令 + `VerifyConnection` |
| `DisconnectSlots` / `DisconnectSlotsById` | $O(1)$ | `LinksMap` 查找 + 连接删除 |
| `PatchNodeProperties` / `PatchComponentById` | $O(P)$ | 反射修补，逐属性拒绝规则 |
| `SetEnumSlotCollection` / `GetEnumSlotByValue` | $O(\text{成员数})$ | 选择器切换重建条目 |
| `ExecuteNode` / `ExecuteNodes` | $O(\text{节点工作量})$ | 等待真正完成 |
| `RunCompiledWorkflow` | $O(V + E)$ 编译 + $O(\text{链工作量})$ | `CompilerViewModel.CompileAsync` + `CompilerEngine.RunAsync` |
| `ListCreatableTypes` | $O(A \cdot T)$ | 扫描程序集找可创建的节点/槽位类型 |
| `ValidateWorkflow` | $O(V + E)$ | 节点/连接遍历 + 重复连接 `HashSet` 去重 |
| `GetNodeStatistics` | $O(S + \text{连接数})$ | 槽位/target/source 遍历 |
| `RequestSelection` / `RequestConfirmation` | $O(1)$ + 处理器 | 用户等待占主导 |
| `TakeSnapshot` / `GetChangesSinceSnapshot` | $O(V \cdot P + E)$ | 见上文 |

*源码：`WorkflowAgentToolkit.cs` —— 各类中的工具主体；`TrackedAIFunction` 第 175-239 行；`QueryToolNames` 第 245-255 行。*

## `McpScope.LoadAsync`

`LoadAsync` 迭代 $N$ 个服务器配置；每服务器成本为安装（本地模式）+ 连接：

$$T_{\text{load}}(N) = \sum_{i=1}^{N} \left( T_{\text{install}}(i) + T_{\text{connect}}(i) \right)$$

**npm 安装幂等。** `EnsureNpmPackageAsync` 以 `"node:{package}@{version}"` 为键，存于进程级 `HashSet`，由全局 `SemaphoreSlim(1,1)` 守卫。记忆化检查为 $O(1)$；首次安装只跑一次 `npm install` 并记录键，因此同一包重复加载在安装层面为 $O(1)$：

$$T_{\text{install}} = \begin{cases} O(\text{npm/pip 工作量}) & \text{首次} \\ O(1) & \text{已记忆化} \end{cases}$$

**stdio 启动 + 握手。** `ConnectServerAsync` 构建 `StdioClientTransport`、创建 MCP 客户端并完成 JSON-RPC `initialize`/`tools/list` 握手。成本由服务器进程启动与工具列表主导：

$$T_{\text{connect}} = O(\text{spawn} + \text{握手} + \text{工具Schema大小})$$

单服务器失败成本 $O(1)$ 且不中止批次（触发 `ServerError` 事件；该服务器贡献 0 个工具）。聚合状态维护（`McpStatusViewModel`）每次状态变化为 $O(1)$，注册了 `SynchronizationContext` 时 marshal 到 UI 线程。

*源码：`McpScope.cs` 的 `LoadAsync` 第 163-187 行、`EnsureNpmPackageAsync` 第 296-328 行、`ConnectServerAsync` 第 378-413 行。*

## 汇总

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `WithAutoDiscovery(assembly)` | $O(T + R \cdot m \cdot k)$ | $O(R)$ 集合 | $T$ 类型、$R$ 已注册、$m$ 成员/组件、$k$ 泛型递归 |
| `WorkflowStateTracker.TakeSnapshot` | $O(V \cdot P + E)$ | $O(V \cdot P + E)$ | 图遍历 + 标量反射 |
| `WorkflowStateTracker` 差异 | $O(V \cdot P' + E)$ | $O(V + E)$ | `RuntimeId` 索引 + 属性 `DeepEquals` |
| 工具包派发开销 | $O(1)$ | $O(1)$ | 追踪包装计数器 + 事件 |
| 查询工具（列表/详情/拓扑） | $O(V \cdot P + E)$ | $O(\text{结果})$ | 节点/槽位/属性遍历 |
| 遍历（`SearchForward`、`FindPath`、`IsConnected`） | $O(V + E)$ | $O(V)$ | BFS + visited/parent |
| `CreateNode` 重叠规避 | 线性 $O(V)$，空间 $O(1)$ | $O(1)$ 暂存 | 查询单元格 $k = O(1)$ 期望 |
| `SetEnumSlotCollection` | $O(\text{成员数})$ | $O(\text{成员数})$ | 选择器切换重建 |
| `RunCompiledWorkflow` | $O(V + E)$ + 链工作量 | $O(V + E)$ | 编译 + 引擎驱动 |
| `McpScope.LoadAsync` | $O(N \cdot (T_{\text{install}} + T_{\text{connect}}))$ | $O(\text{工具})$ | 首次后安装记忆化 $O(1)$ |
