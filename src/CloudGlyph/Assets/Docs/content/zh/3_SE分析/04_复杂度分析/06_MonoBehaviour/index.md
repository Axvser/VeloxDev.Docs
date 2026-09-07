# 复杂度分析 — MonoBehaviour

下面的每帧复杂度界适用于拥有 $b$ 个活动行为、并由其更新驱动与固定驱动驱动的通道。`MonoBehaviourManager.cs` 的行号对应当前源码。

## 每帧分发

$$
O(b), \quad b = \text{活动行为数}
$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` 对缓存的包装器数组遍历一次，逐个调用 `InvokeUpdate` / `InvokeLateUpdate` / `InvokeFixedUpdate` —— `MonoBehaviourManager.cs` 第 611-657 行。

包装器数组由 `GetCachedWrappers`（第 663-673 行）在注册 / 移除触发排序标记时或每 `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms 重建一次；重建会复制活动包装器并按 `ExecutionOrder` 插入排序（`RebuildCachedWrappers`，第 805-834 行）。行为数量通常很小，因此每帧排序代价被摊还掉：

$$
T_{\text{update}} = O(b) \text{ 每帧}, \quad b \ll n_{\text{registered}}
$$

当某行为把 `FrameEventArgs.Handled` 置 `true` 时，循环提前 break，实际代价变为 $O(k)$，其中 $k$ 是短路前已执行的行为数（$k \le b$）。

## 固定更新间隔

$$
O(b) \text{ 每约 } \approx \text{interval 毫秒}
$$

固定驱动与更新驱动并发运行 `ExecuteBehaviorsFixedUpdateSync`，按 `SetFixedUpdateInterval` 间隔驱动（默认 `DEFAULT_FIXED_UPDATE_INTERVAL_MS = 16`）。其稳态代价与帧率无关 —— 物理 / 固定时间步逻辑与渲染 FPS 解耦。

## 事件参数复用（对象池）

每帧更新驱动调用 `CreateFrameEventArgs`（第 745-755 行），从每通道 `ObjectPool<FrameEventArgs>`（默认 `DEFAULT_OBJECT_POOL_SIZE = 50`）取出而非重新分配：

$$
O(1) \text{ 每帧取/还，稳态零分配}
$$

对象池是无锁 `ConcurrentStack` 且有界容量，被两个驱动共享（固定事件来自同一池）。未被处理的 `FixedUpdate` 事件入队，由更新驱动在下一帧开头排空时归还（`DrainFixedUpdateEvents`，第 757-761 行）；已处理者立即归还。`ConfigChangeRequest` 与 `BehaviorWrapper` 对象来自各自同容量的池，因此注册 / 配置抖动也不会造成稳态分配。

## 帧节奏控制

`FrameRateControlSync` 睡眠到目标帧时长（`_cachedTargetFrameDurationTicks`，在应用 `TargetFPS` 时更新）。`PrecisionSleep` 低于 `SPIN_ONLY_THRESHOLD_MS = 2` ms 时纯自旋，否则 `Thread.Sleep(1)` + 尾部自旋 —— 第 763-803 行。每帧墙钟时间 $O(1)$。异步循环模式下同样的节奏控制是 `Task.Delay`（最小 1 ms），帧超时时用 `Task.Yield`（`UpdateLoopAsync`，第 548-605 行）。

## 配置 / 注册批处理

配置变更、行为增删与转发的“主线程”动作通过并发队列交换，由 `ProcessMainThreadOperations`（第 675-688 行）每帧排空一次：

| 操作 | 每帧 |
|---|---|
| `SetTargetFPS` / `SetFixedUpdateInterval` / `SetTimeScale` | 池化入队 $O(1)$；每帧排空 $O(q)$，$q$ = 待处理请求数 |
| `RegisterBehaviour` / `UnregisterBehaviour` | 入队 $O(1)$；每帧排空 $O(r)$，$r$ = 待处理注册数 |
| `ExecuteOnMainThread` | 入队 $O(1)$；每帧最多排空 64 个 |
| `Pause` / `Resume` / `Stop` | volatile 写 + 事件引发 $O(1)$（不入队） |

## 内存

| 结构 | 行为 |
|---|---|
| 缓存包装器数组 | $O(b)$ 个 `BehaviorWrapper[]`，变更时或每 1000 ms 重建 |
| 对象池 | 3 个池（`FrameEventArgs`、`ConfigChangeRequest`、`BehaviorWrapper`），每通道固定容量 50；复用实例，不产生垃圾 |
| 并发队列 | $O(q)$ 配置 / $O(r)$ 注册 / $O(a)$ 主线程动作，每帧排空；`_fixedUpdateEvents` 于下一更新帧排空 |
| 驱动 | 每通道 2 个 —— 线程模式为线程，异步循环模式为异步任务 |

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| `Update` / `LateUpdate` 分发（每帧） | $O(b)$ |
| `FixedUpdate` 分发 | 每固定间隔（约 16 ms）$O(b)$ |
| `Start` / `StopAsync` | $O(b + q)$（构建 / 清理结构） |
| 配置设置器（`SetTargetFPS`、`SetTimeScale` 等） | 池化入队 $O(1)$ |
| `RegisterBehaviour` / `UnregisterBehaviour` | 入队 $O(1)$；缓存数组重建 $O(b)$（摊还） |
| `ExecuteOnMainThread` | 入队 $O(1)$；每帧 ≤ 64 个排空 |
| `FrameEventArgs` 创建 | $O(1)$ 池化 —— 稳态零分配 |
