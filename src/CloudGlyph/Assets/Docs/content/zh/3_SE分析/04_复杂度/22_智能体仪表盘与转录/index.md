# 智能体仪表盘与转录

转录是一份只追加的文本结构；仪表盘是活作用域的投影。两者按事件都很便宜，按整遍都很贵。唯一的渐进风险是字符串拼接：追加一个片段会复制整个答案，所以调用方的投递频率决定转录是线性增长还是二次增长。

## 代价模型

| 符号 | 含义 |
|---|---|
| $e$ | 通过管线发布的事件数 |
| $k$ | 管线级数 |
| $t$ | 转录条目数 |
| $L$ | 当前答案长度 |
| $B$ | 文本管线的落盘阈值（1024 字符） |
| $M$ | 仪表盘成员：工具、服务器、服务器工具、技能 |
| $m$ | 媒体附件数 |
| bytes | 媒体负载字节数 |

## 管线分发

`AgentPipeline.PublishAsync` 调用第 0 级，并传入一个调用第 1 级的 `next` 闭包，依此类推。每一级各自包在 `try/catch` 里，异常归属于抛出的那一级（`Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/AgentPipeline.cs:89-107`）。

```csharp
private async ValueTask InvokeAsync(int index, AgentEvent agentEvent, CancellationToken cancellationToken)
{
    if (index >= _stages.Count) return;

    var stage = _stages[index];
    try
    {
        // A failure further down is caught at its own level, so anything caught here belongs to this
        // stage — which keeps the attribution honest.
        await stage.OnEventAsync(
            agentEvent,
            next => InvokeAsync(index + 1, next, cancellationToken),
            cancellationToken).ConfigureAwait(false);
    }
```

每个事件的代价是

$$
T_{\text{publish}} = O(k)
$$

每级每事件各一个闭包和一个 `ValueTask` 状态机。整条链严格串行：慢级会反压整次运行。

## 转录追加

`AgentTranscriptEntry.Append` 就是 `Text += fragment` —— 对整个答案的不可变复制（`Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/AgentTranscript.cs:147-151`）。文档注释写明了契约：每次调用复制整个答案，调用频率由调用方负责。

```csharp
internal void Append(string fragment)
{
    if (string.IsNullOrEmpty(fragment)) return;
    Text += fragment;
}
```

逐片段调用的代价是

$$
T_{\text{append}} = O(L^2)
$$

对于长度为 $L$ 的答案。`TextPipeline` 用 `StringBuilder` 缓冲片段，只在 1024 字符或角色边界处落盘（`Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/TextPipeline.cs:135-153`），把转录代价降到 $O(L^2 / B)$。

```plot
{
  "title": "不同投递频率下的答案物化",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 10000] },
  "data": [
    { "fn": "x^2", "color": "#f472b6", "title": "逐片段调用" },
    { "fn": "x^2/1024", "color": "#a78bfa", "title": "1024 字符批量" },
    { "fn": "x", "color": "#4a9eff", "title": "线性下界" }
  ]
}
```

## 转录导出

| 操作 | 时间 | 空间 |
|---|---|---|
| `ToMarkdown` | $O(t + \sum \text{text} + \sum \text{rendered detail})$ | $O(\text{输出})$ |
| `ToJson` | $O(t + \text{text bytes} + m)$ | $O(\text{输出})$ |
| `ToPlainTextLines` | $O(t + \text{bytes})$ | $O(t + \text{bytes})$ |
| `Restore` | $O(\text{json bytes} + t + m)$ | $O(t + m + \text{text})$ |

每次导出都重建整份文档；没有脏标记，也没有缓存渲染。默认 Markdown 路径不内联工具 `Detail`，所以工具正文不进入输出代价；开启 `ChatFences` 后，每个工具正文最多复制 4000 字符的详情上限。

## 仪表盘重建

`AgentDashboardViewModel.Rebuild` 依次重建五个集合，再重建汇总（`Src/Core/VeloxDev.Core.Extension/Agent/Dashboard/AgentDashboardViewModel.cs:172-182`）。

$$
T_{\text{rebuild}} = O(T + S + \text{MCP tools} + n)
$$

每次作用域 `Changed` 与每次子智能体行变化都会排队一次重建（`:113`、`:205`）。行按名称复用并保留已有视图模型，但每一遍都会清空再重加绑定集合，所以即使什么都没变，消费者也会收到重置通知。

`RecordCall` 扫描全部成员以找到刚运行的工具（`:123-141`），于是一次工具调用在 UI 线程上花 $O(M)$。`CallSummary` 每次通知又重走同一批成员，再花 $O(M)$。

## 媒体

`AgentMedia.FromBytes` 复制负载、按魔数检测格式，并读取图像尺寸（`Src/Core/VeloxDev.Core.Extension/Agent/Media/AgentMedia.cs:96-128`）。

$$
T_{\text{attach}} = O(\text{bytes})
$$

对文本类与动图格式的嗅探窗口至多 4096 字节（`Src/Core/VeloxDev.Core.Extension/Agent/Media/AgentMediaFormat.cs:92-118`）。PNG、GIF、BMP、WebP 的头部读取是常数时间；JPEG 读取器要遍历段标记，是唯一最坏情况与缓冲区成正比的嗅探器（`Agent/Media/ImageHeaderReader.cs:16-38`）。

摄入复制一次，流路径多一次中间 `ToArray()`，`FromDataUri` 还有子串与解码的临时副本，`ToBase64String` 在编码前再复制一次 —— 大附件可能同时持有两到三份完整副本。`CreateUserAsync` 在 `foreach` 中逐个规范化附件，所以 $m$ 个负载的转码耗时是各自时间之和而不是最大值（`Agent/Media/AgentMessage.cs:93-110`）。

## 相关

- [子智能体](../21_子智能体/index.md) —— 仪表盘投影的状态行。
- [MCP集成](../20_MCP集成/index.md) —— 服务器与工具行。
