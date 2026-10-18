# 复杂度分析 —— 工作流代理

## `WithAutoDiscovery` 的上下文树遍历

发现**不是**程序集扫描。源码生成器已经遍历编译并把类型分类进 agent 上下文树，因此 `WithAutoDiscovery` 只是对 `Customer/` 下（`Enums`、`Interfaces`、`Data`、`Components/{kind}`）做固定次数的目录列举，并解析每个被收录的类型字面量。设 $R$ 为注册条目数、$L$ 为目录列举数：

$$
T_{\text{discovery}} = O(R + L), \qquad S_{\text{discovery}} = O(R_{\text{comp}} + R_{\text{enum}} + R_{\text{iface}} + R_{\text{data}})
$$

注册桶是 `HashSet`，因此跨语言去重（`_globallyDiscoveredTypes`）让重复调用为 $O(R)$ 且不产生新分配。运行时不对任何东西做反射；生成器从未收录的类型就是不存在。

*源码：`WorkflowAgentScope.cs` 的 `WithAutoDiscovery` / `RegisterDiscovered`。*

## `WorkflowStateTracker.TakeSnapshot` / 差异

`BuildSnapshot` 遍历整张图：$V$ 个节点与 $E$ 条可见链接。对每个节点它发射标量属性（每节点 $P$ 个）并生成 JSON 树：

$$
T_{\text{snapshot}} = O(V \cdot P + E), \qquad S_{\text{snapshot}} = O(V \cdot P + E)
$$

`ComputeDiff` 为节点与链接构建 `RuntimeId → VeloxJsonObject` 字典，耗时 $O(V + E)$，随后逐节点比较标量/枚举属性：

$$
T_{\text{diff}} = O(V + E + V \cdot P') = O(V \cdot P' + E)
$$

其中 $P' \le P$ 是 JSON 中的标量属性数。只捕获标量与枚举属性，因此差异从不物化完整子树比较。

*源码：`WorkflowStateTracker.cs` 的 `BuildSnapshot`、`ComputeDiff`、`IndexById`。*

## 工具包派发

每个工具都被 `TrackedAIFunction` 包装，每次调用开销为 $O(1)$（计数器 + 事件 + 可选 `MarkDirty`）。预检闸门 `CheckInvocation` 为 $O(1)$：`IsToolEnabled` 哈希探测、一次策略评估、可选的根账本行走、三次整数比较。工具体占主导：

$$
T_{\text{tool}} = O(\text{per-tool work}), \qquad T_{\text{tracked}} = T_{\text{tool}} + O(1)
$$

### 逐工具复杂度

| 工具 | 时间 | 依据 |
|---|---|---|
| `ListNodes` / `FindNodes` | $O(V \cdot P)$ | 单遍节点，逐节点标量属性 |
| `GetNodeDetail` / `GetNodeDetailById` | $O(P + S)$ | 单节点，$S$ 个槽（按 id 另有 $O(V)$ id 扫描） |
| `GetFullTopology` | $O(V \cdot (P + S) + E)$ | 整张图 |
| `ListConnections` / `ListSlotProperties` | $O(L)$ / $O(V \cdot P + S)$ | 链接 / 节点+属性 |
| `GetWorkflowSummary` | $O(V)$ | 不同类型名一遍 |
| `SearchForward` / `SearchReverse` / `SearchAllRelative` / `IsConnected` / `FindPath` | $O(V + E)$ | 带 visited/parent 映射的 BFS |
| `CreateNode` | 期望 $O(V)$，有空间映射时 $O(1)$ | 重叠扫描 |
| `MoveNode` / `SetNodePosition` / `ResizeNode` / `DeleteNode` / `DeleteSlot` | $O(1)$ | 一次命令派发 + 等待 |
| `ConnectSlots` / `ConnectSlotsById` / `ConnectByProperty` | 摊还 $O(1)$ | 槽解析 + Send/Receive 命令 + `VerifyConnection` |
| `PatchNodeProperties` / `PatchComponentById` | $O(P)$ | 反射补丁，逐属性拒绝规则 |
| `RunCompiledWorkflow` / `GetNodeResult` | 编译 + 链/锥工作 | 见下 |
| `ListCreatableTypes` | $O(A \cdot T)$ | 编译后的上下文树查找 |
| `ValidateWorkflow` | $O(V + E)$ | 带重复链接去重的节点/链接遍历 |
| `RequestSelection` / `RequestConfirmation` | $O(1)$ + 处理器 | 用户等待占主导 |
| `TakeSnapshot` / `GetChangesSinceSnapshot` | $O(V \cdot P + E)$ | 见上 |

*源码：`WorkflowAgentToolkit.cs` 的工具体；`TrackedAIFunction.cs`；`QueryToolNames`。*

## 编译运行 / 终结点结果

两个链入口共用 `RunCompiledRoleAsync`（`WorkflowAgentToolkit.cs`）。编译步骤从树构建编译图；Root 运行随后驱动整条可达链，Terminal 运行只驱动被查询节点的祖先锥（因此其编译与运行成本随锥而变，而非整棵树）：

$$
T_{\text{Root}} = O\big(V + E\big)_{\text{compile}} + O(\text{chain work}), \qquad
T_{\text{Terminal}} = O\big(V_{\text{cone}} + E_{\text{cone}}\big)_{\text{compile}} + O(\text{cone work})
$$

引擎维护运行时会话（`RuntimeContext`）：每次驱动步骤的记账（`Status`、`Attempt`、`Outcome`、`Logs`）为 $O(1)$，日志为 $O(\text{steps})$。前向一致的 Terminal 契约 —— 路由器选兄弟分支意味着 `TargetReached = false` 并返回显式 `error`，**没有**伪造值 —— 运行后检查成本为 $O(1)$。

## 运行句柄家族

句柄注册表是一把锁保护的 `Dictionary<string, CompiledRun>`；句柄分配是 `Interlocked.Increment`。逐次调用：

- `StartCompiledWorkflow` / `ContinueCompiledWorkflow`：一次编译（如上）+ 一次 `Dictionary` 写入 —— 由编译主导，$O(V+E)$。
- `GetCompiledRunStatus`：`SnapshotLogs()` 在日志锁下为 $O(\log)$（保留列表的副本），随后取 $\min(40, L)$ 行尾部；注册表读/移除期望 $O(1)$。日志尾部内存被 `RunStatusLogTail = 40` 约束。

$$
T_{\text{status}} = O(\min(40, L)) + O(1), \qquad S_{\text{tail}} = O(40)
$$

- `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`：$O(1)$ —— 闸门标志翻转或 `CancellationTokenSource.Cancel`。

`ContinueCompiledWorkflow` 另加一次检查点加载，$O(\text{checkpoint size})$。

## `ToolCallLedger` 链

`Spend` 递归到 `Outer`，因此一次调用的成本是账本链深度：

$$
T_{\text{spend}} = O(d), \qquad S_{\text{ledger}} = O(d)
$$

其中 $d$ 是 spawn 深度（受子代理深度限制约束）。`ResetChain` 同样为 $O(d)$。`Usage` 是三次无锁 `Volatile.Read`，$O(1)$。

## `WorkflowAgentContextProvider` 渲染缓存

`BuildContext` 先读 `Scope.ContextKey`（$O(1)$：一次 `Version` 读取、树的选中集 revision 与预算档计算），并与已发布键比较。命中时无锁、无分配地返回上一个 `AIContext`。未命中时重建指令，且仅在 `Version` 移动时重建工具列表：

$$
T_{\text{render}} = \begin{cases} O(1) & \text{cache hit} \\ O(\text{instructions} + |\text{tools}|) & \text{cache miss} \end{cases}
$$

能力包络测试直接测量未命中成本：包络比静态骨架小一个数量级，1000 个空闲轮次分配 **0 字节**。

## `McpScope.LoadAsync`

`LoadAsync` 遍历 $N$ 份服务器配置；每台服务器的成本是安装（本地模式）+ 连接：

$$
T_{\text{load}}(N) = \sum_{i=1}^{N} \left( T_{\text{install}}(i) + T_{\text{connect}}(i) \right)
$$

**npm/pip 安装幂等。** `EnsureNpmPackageAsync` 以 `"node:{package}@{version}"`（pip 为 `"py:..."`）为键，存在进程级列表并由全局 `SemaphoreSlim(1,1)` 保护。首次安装后记忆化检查为 $O(1)$：

$$
T_{\text{install}} = \begin{cases} O(\text{npm/pip work}) & \text{first time} \\ O(1) & \text{memoized} \end{cases}
$$

**传输 + 握手。** `ConnectServerAsync` 执行 JSON-RPC `initialize`/`tools/list` 握手；成本由进程启动与工具列表主导，$O(\text{spawn} + \text{handshake} + \text{toolSchemaSize})$。单服务器失败成本 $O(1)$，且不中止整批。

## 汇总

| 操作 | 时间 | 空间 | 依据 |
|---|---|---|---|
| `WithAutoDiscovery()` | $O(R + L)$ | $O(R)$ 集合 | 上下文树目录列举，$R$ 条目，$L$ 列举 |
| `WorkflowStateTracker.TakeSnapshot` | $O(V \cdot P + E)$ | $O(V \cdot P + E)$ | 图遍历 + 标量属性发射 |
| `WorkflowStateTracker` 差异 | $O(V \cdot P' + E)$ | $O(V + E)$ | `RuntimeId` 索引 + 属性比较 |
| 工具包派发开销 | $O(1)$ | $O(1)$ | 跟踪包装器计数 + 事件 |
| `CheckInvocation` 闸门 | $O(1)$（到根为 $O(d)$） | $O(1)$ | 哈希探测 + 策略 + 整数比较 |
| `ToolCallLedger.Spend` / `ResetChain` | $O(d)$ | $O(d)$ | 沿 spawn 链行走 |
| 提供器渲染 | 命中 $O(1)$ / 未命中 $O(\text{text} + n_{\text{tools}})$ | 命中 $O(1)$ | `ContextKey` 缓存 |
| `GetCompiledRunStatus` | $O(\min(40, L))$ | $O(40)$ | `SnapshotLogs()` + 尾部 |
| `StartCompiledWorkflow` | $O(V + E)$ 编译 + $O(1)$ | $O(V + E)$ | 编译主导 |
| `Pause` / `Resume` / `StopCompiledRun` | $O(1)$ | $O(1)$ | 闸门标志 / token 取消 |
| `McpScope.LoadAsync` | $O(N \cdot (T_{\text{install}} + T_{\text{connect}}))$ | $O(\text{tools})$ | 首次加载后安装记忆化为 $O(1)$ |
