# 复杂度 — Tickable

本特性的成本模型有个不寻常之处：几乎没有任何东西随帧率增长。每帧工作是行为数的线性函数、常数很小；看起来昂贵的部分（注册后重排、重建快照）发生在变更时，而不是每帧。

设 $N$ 为一个通道上注册的行为数，$F$ 为目标帧率，$h$ 为固定步长（毫秒）。

## 汇总

| 操作 | 时间 | 空间 | 受限于 |
|---|---|---|---|
| 每帧 `Update` + `LateUpdate` 扫描 | $O(N)$ | $O(1)$ | $N$，不是 $F$ |
| 每步 `FixedUpdate` 扫描 | 每步 $O(N)$ | $O(1)$ | $N$ |
| `RegisterBehaviour`（调用方侧） | 均摊 $O(1)$ | $O(1)$ | `ConcurrentQueue<T>` 入队 |
| 注册排空（泵侧） | 最坏 $O(N^2)$，通常 $O(N)$ | 每行为 $O(1)$ | 有新增的排空会触发一次重建 |
| `RebuildCachedWrappers` | 最坏 $O(N^2)$ | $O(N)$ | 插入排序 —— 因为 $N$ 很小 |
| `GetCachedWrappers` 缓存命中 | $O(1)$ | — | 一次 `Stopwatch.GetTimestamp` |
| 状态查询 | 期望 $O(1)$ | $O(1)$ | `ConcurrentDictionary` 哈希查找 |
| 池 `Get` / `Return` | $O(1)$ | $O(1)$ | 无锁 `ConcurrentStack<T>` |

## 数字从哪来

- 派发数组每次扫描读一次、按索引遍历，所以一次扫描恰好是 $N$ 次迭代，每次做一次委托调用加一次 `Handled` 检查。`Handled` 可以提前截断，所以*最坏*是 $O(N)$，常见情况更小。
- 注册是均摊的：调用方付一次入队，泵付一次字典插入加一次插入排序。排序最坏 $O(N^2)$，但只在排空置起 `_wrappersNeedSort` 时运行；源码指出行为数量足够小，避免 LINQ 分配比 $O(N \log N)$ 排序更值。
- `MAX_CONFIG_CACHE_DURATION_MS` 刷新（1 秒）意味着缓存几乎每帧都按时间戳重新验证，但只在变更时重建。

## 子页

| 子页 | 覆盖 |
|---|---|
| [帧派发](00_帧派发/index.md) | 每帧与每步扫描、`Handled` 短路、均摊的缓存验证 |
| [固定步长节拍](01_固定步长节拍/index.md) | 补偿采样器的算术、欠账上界、睡眠为何分片 |
| [注册表与池化](02_注册表与池化/index.md) | 通道注册表查找、写时复制快照、三个池 |

## 值得随身带的一个公式

目标帧率 $F$、步长 $h$ ms 时，一个通道每秒大约交付

$$
\text{deliveries per second} \approx F \cdot (2N) + \frac{1000}{h} \cdot N
$$

第一项是 update 与 late 扫描，第二项是固定步 —— 注意固定步频率是 $1000/h$，与 $F$ 无关。示例直接报告这个比值作为「每帧步数」：WPF 示例在一秒窗口内测量 $\Delta \text{fixed} / \Delta \text{frames}$ 并显示，测量的意义在于按下帧率按钮时它几乎不动（`MainWindow.xaml.cs` 第 170-197 行）。
