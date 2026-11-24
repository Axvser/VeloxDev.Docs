# Agent Dashboard and Transcript

The transcript is an append-only text structure; the dashboard is a projection of live scopes. Both are cheap per event and expensive per full pass. The one asymptotic hazard is string concatenation: appending one fragment copies the whole answer, so the caller's delivery rate decides whether the transcript grows linearly or quadratically.

## Cost model

| Symbol | Meaning |
|---|---|
| $e$ | events published through a pipeline |
| $k$ | stages in the pipeline |
| $t$ | transcript entries |
| $L$ | length of the open answer |
| $B$ | flush threshold of the text pipeline (1024 chars) |
| $M$ | dashboard members: tools, servers, server tools, skills |
| $m$ | media attachments |
| bytes | media payload size |

## Pipeline dispatch

`AgentPipeline.PublishAsync` invokes stage 0, passing a `next` closure that invokes stage 1, and so on. Each stage is wrapped in its own `try/catch` so a failure is attributed to the stage that threw (`Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/AgentPipeline.cs:89-107`).

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

Cost per event is

$$
T_{\text{publish}} = O(k)
$$

with one closure and one `ValueTask` state machine per stage per event. The chain is strictly sequential: a slow stage back-pressures the run.

## Transcript append

`AgentTranscriptEntry.Append` is `Text += fragment` — an immutable copy of the whole answer (`Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/AgentTranscript.cs:147-151`). The doc comment states the contract: every call copies the whole answer, and the caller owns the call rate.

```csharp
internal void Append(string fragment)
{
    if (string.IsNullOrEmpty(fragment)) return;
    Text += fragment;
}
```

Per-fragment callers pay

$$
T_{\text{append}} = O(L^2)
$$

for an answer of length $L$. `TextPipeline` batches fragments in a `StringBuilder` and delivers only at 1024 characters or at a role boundary (`Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/TextPipeline.cs:135-153`), reducing the transcript cost to $O(L^2 / B)$.

```plot
{
  "title": "Answer materialisation per delivery rate",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 10000] },
  "data": [
    { "fn": "x^2", "color": "#f472b6", "title": "one call per fragment" },
    { "fn": "x^2/1024", "color": "#a78bfa", "title": "batched at 1024" },
    { "fn": "x", "color": "#4a9eff", "title": "linear lower bound" }
  ]
}
```

## Transcript export

| Operation | Time | Space |
|---|---|---|
| `ToMarkdown` | $O(t + \sum \text{text} + \sum \text{rendered detail})$ | $O(\text{output})$ |
| `ToJson` | $O(t + \text{text bytes} + m)$ | $O(\text{output})$ |
| `ToPlainTextLines` | $O(t + \text{bytes})$ | $O(t + \text{bytes})$ |
| `Restore` | $O(\text{json bytes} + t + m)$ | $O(t + m + \text{text})$ |

Every export rebuilds the whole document; there is no dirty flag or cached rendering. In the default Markdown path tool `Detail` is not inlined, so tool bodies do not enter the output cost. With `ChatFences` on, each tool body is copied up to the 4000-character detail limit.

## Dashboard rebuild

`AgentDashboardViewModel.Rebuild` sequentially rebuilds five collections and then the aggregates (`Src/Core/VeloxDev.Core.Extension/Agent/Dashboard/AgentDashboardViewModel.cs:172-182`).

$$
T_{\text{rebuild}} = O(T + S + \text{MCP tools} + n)
$$

Every scope `Changed` and every sub-agent row change queues a rebuild (`:113`, `:205`). Row reuse is by name and preserves existing view models, but each pass clears and re-adds its bound collections, so consumers see reset notifications even when nothing changed.

`RecordCall` scans all members to find the tool that ran (`:123-141`), making a tool call cost $O(M)$ on the UI thread. `CallSummary` re-walks the same members per notification, another $O(M)$.

## Media

`AgentMedia.FromBytes` copies the payload, detects the format from magic numbers, and reads image dimensions (`Src/Core/VeloxDev.Core.Extension/Agent/Media/AgentMedia.cs:96-128`).

$$
T_{\text{attach}} = O(\text{bytes})
$$

with a sniff window of at most 4096 bytes for text-like and animated formats (`Src/Core/VeloxDev.Core.Extension/Agent/Media/AgentMediaFormat.cs:92-118`). PNG, GIF, BMP and WebP header reads are constant-time; the JPEG reader walks segment markers and is the only sniffer whose worst case is proportional to the buffer (`Agent/Media/ImageHeaderReader.cs:16-38`).

Ingest copies once, stream paths add an intermediate `ToArray()`, `FromDataUri` adds substring and decode transients, and `ToBase64String` copies again before encoding — a large attachment can transiently hold two to three full copies. `CreateUserAsync` normalises each attachment in a `foreach`, so transcoding $m$ payloads costs the sum of their times, not the maximum (`Agent/Media/AgentMessage.cs:93-110`).

## Related

- [Sub-Agents](../21_sub-agents/index.md) — the status rows this dashboard projects.
- [MCP Integration](../20_mcp-integration/index.md) — the server and tool rows.
