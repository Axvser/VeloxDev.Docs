# 复杂度分析 — MonoBehaviour

## 每帧分发

$$O(b), \quad b = \text{活动行为数}$$

`ExecuteBehaviorsUpdateSync` / `ExecuteBehaviorsLateUpdateSync` / `ExecuteBehaviorsFixedUpdateSync` 对缓存的包装器数组遍历一次，逐个调用 `InvokeUpdate` / `InvokeLateUpdate` / `InvokeFixedUpdate` —— `MonoBehaviourManager.cs` 第 610-656 行。

包装器数组只在行为增删或每 `MAX_CONFIG_CACHE_DURATION_MS = 1000` ms 重建一次；重建本身是对小型数组的插入排序（行为数量通常很小），因此每帧排序代价被摊还掉：

$$T_{\text{update}} = O(b) \text{ 每帧}, \quad b \ll n_{\text{registered}}$$

当某行为把 `FrameEventArgs.Handled` 置 `true` 时，循环提前 break，实际代价变为 $O(k)$，其中 $k$ 是短路前已执行的行为数（$k \le b$）。

## 固定更新间隔

$$O(b) \text{ 每约 } \approx \text{interval 毫秒}$$

`ExecuteBehaviorsFixedUpdateSync` 在固定线程上按 `SetFixedUpdateInterval` 毫秒（默认 `DEFAULT_FIXED_UPDATE_INTERVAL_MS = 16`）运行。其稳态代价与帧率无关 —— 物理 / 固定时间步逻辑与渲染 FPS 解耦。

## 事件参数复用（对象池）

每帧调用 `CreateFrameEventArgs`，从每通道 `ObjectPool<FrameEventArgs>`（默认 `DEFAULT_OBJECT_POOL_SIZE = 50`）取出而非重新分配：

$$O(1) \text{ 每帧取/还，稳态零分配}$$

未处理的 `FixedUpdate` 事件入队，由 Update 线程排空时归还对象池（`DrainFixedUpdateEvents`，第 756-760 行），因此每帧不会有 `FrameEventArgs` 逃逸。

## 帧节奏控制

`PrecisionSleep` 低于 `SPIN_ONLY_THRESHOLD_MS = 2` ms 时纯自旋，否则 `Thread.Sleep(1)` + 尾部自旋 —— `MonoBehaviourManager.cs` 第 777-802 行。每帧墙钟时间 $O(1)$。

## 配置 / 注册批处理

配置变更、行为增删与主线程动作通过并发队列交换，每帧排空一次：

| 操作 | 每帧 |
|---|---|
| `SetTargetFPS` / `SetFixedUpdateInterval` / `SetTimeScale` | $O(1)$ 入队；每帧排空 $O(q)$，$q$ = 待处理请求数 |
| `RegisterBehaviour` / `UnregisterBehaviour` | $O(1)$ 入队；每帧排空 $O(r)$，$r$ = 待处理注册数 |
| `ExecuteOnMainThread` | $O(1)$ 入队；每帧最多排空 64 个 |

## 内存

| 结构 | 行为 |
|---|---|
| 缓存包装器数组 | $O(b)$ 个 `BehaviorWrapper[]`，变更时或每 1000 ms 重建 |
| `FrameEventArgs` 池 | 每通道固定容量 50；复用池化实例，不产生垃圾 |
| 并发队列 | $O(q)$ 配置 / $O(r)$ 注册 / $O(a)$ 主线程动作，每帧排空 |
| 线程 | 每通道 2 个线程（`UseAsyncLoop` 时为 2 个异步任务） |
| 包装对象 | `BehaviorWrapper` 与 `ConfigChangeRequest` 本身也池化 |

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| `Update` / `LateUpdate` 分发（每帧） | $O(b)$ |
| `FixedUpdate` 分发 | 每固定间隔（约 16 ms）$O(b)$ |
| `Start` / `StopAsync` | $O(b + q)$（构建 / 清理结构） |
| 配置设置器（`SetTargetFPS`、`SetTimeScale` 等） | $O(1)$ |
| `RegisterBehaviour` / `UnregisterBehaviour` | $O(1)$ 入队；缓存数组重建 $O(b)$（摊还） |
| `ExecuteOnMainThread` | $O(1)$ 入队；每帧 ≤ 64 个排空 |
| `FrameEventArgs` 创建 | $O(1)$ 池化 —— 稳态零分配 |
