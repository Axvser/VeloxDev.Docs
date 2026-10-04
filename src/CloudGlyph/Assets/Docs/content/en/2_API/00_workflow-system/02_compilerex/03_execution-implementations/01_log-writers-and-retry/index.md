# Workflow System — Log Writers and the Retry Policy

The two implementations that carry real behavior instead of forwarding to a delegate: `TextWriterLogWriter` (the file-backed `ILogWriter`) and `ExponentialBackoffRetry` (the default `INodeRetryPolicy`).

Sources: `Runtime/Model/LogWriters.cs`, `Runtime/Model/RetryPolicies.cs`.

---

## `DelegateLogWriter`

**Signature:** `public sealed class DelegateLogWriter(Action<string> write) : ILogWriter`

The one-liner form for tests and hosts that already have a sink. `Write` calls `_write(line)` — once per line, on the thread driving the run. The constructor throws `ArgumentNullException` when `write` is `null`.

---

## `TextWriterLogWriter`

**Signature:** `public sealed class TextWriterLogWriter : ILogWriter, IDisposable`

An `ILogWriter` that appends to a `System.IO.TextWriter` — the usual case being a file opened for append.

| Member | Type | Description |
|---|---|---|
| constructor | `TextWriterLogWriter(TextWriter writer)` | Wraps an existing writer, which this instance will **not** close. Throws `ArgumentNullException` when `writer` is `null`. |
| `For(string path)` | `static TextWriterLogWriter` | Opens (or creates) `path` for appending, UTF-8 **without** a byte-order mark. The returned instance owns the stream. |
| `Path` | `string?` | The file this writer appends to, as an absolute path; `null` for one wrapped around a `TextWriter` the host already owned. |
| `Write(string line)` | `void` | Appends one line and **flushes**, so a host reading the file sees it without waiting for a buffer. |
| `Dispose()` | `void` | Flushes, and closes the file when this instance opened it — a borrowed `TextWriter` is left open for its owner. |

#### `TextWriterLogWriter.For`

**Signature:** `public static TextWriterLogWriter For(string path)`

| Parameter | Type | Description |
|---|---|---|
| `path` | `string` | The log file. Its directory must exist. |

**Returns:** `TextWriterLogWriter` — a writer that owns the stream; dispose it to flush and close.

**Exceptions:** `FileNotFoundException` / `DirectoryNotFoundException` from the underlying `FileStream` when the directory does not exist. (The demo creates its scratch directory before opening the writer, precisely because of this.)

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
// and in Dispose():
_logWriter?.Dispose();
```

**Verified behavior** (reproduced against the shipped library):

```text
[9] logfile: path=C:\Users\Axvse\AppData\Local\Temp\veloxqs-run.log
[9] logfile: fileLines=3 retained=2 snapshot=2
[9] retained: 02. BiasNode | 03. PrinterNode
[9] file head: 01. TickerNode
```

The file holds all three lines while `MaxRetainedLogs = 2` kept only the two newest in memory — the writer is the full-fidelity record, `Logs` is the bounded view. `CompilerLogWriterTests.MaxRetainedLogs_KeepsTheNewestLines_AndTheWriterLosesNothing` and `TextWriterLogWriter_For_AppendsWithoutABom` pin the same contract.

**Notes:**

- **Whoever opens the stream closes it.** A writer built on a `TextWriter` someone else handed in never closes that writer — the host keeps appending across runs with it. One built by `For` opened the file itself, so disposing it flushes and closes. Disposing either kind flushes.
- `Path` is exposed so a host can tell somebody *where* the log went without also handing over the writer: an Agent asked to read a run's log needs a path to open, and it has no other way to learn one.
- It is called on the thread driving the run — normally the host's UI thread. Wrap it in your own queue if the IO must not happen there.

---

## `ExponentialBackoffRetry`

**Signature:** `public sealed class ExponentialBackoffRetry : INodeRetryPolicy`

Retries a failed node a fixed number of times, doubling the wait each round. The default a host gets when it asks for retries without wanting to write a policy.

| Member | Signature | Description |
|---|---|---|
| constructor | `ExponentialBackoffRetry(int maxAttempts = 3, double baseDelayMs = 200, double factor = 2.0, double maxDelayMs = 5000)` | — |
| `MaxAttempts` | `int` | The number of attempts a node gets **in total**, the first one included. |
| `NextRetryAsync` | `Task<TimeSpan?> NextRetryAsync(NodeFailure failure, CancellationToken ct)` | Returns the delay, or `null` once the attempts are used up. |

**Constructor parameters:**

| Parameter | Type | Description |
|---|---|---|
| `maxAttempts` | `int` | How many attempts in total, the first included — `3` means "try, retry, retry". Clamped to at least `1`. |
| `baseDelayMs` | `double` | The wait before the first retry, in milliseconds. Clamped to at least `0`. |
| `factor` | `double` | What each successive wait is multiplied by. Clamped to at least `1`. |
| `maxDelayMs` | `double` | A ceiling on a single wait, so a long chain of retries stays bounded. Clamped to at least `baseDelayMs`. |

**Delay formula:**

$$
d_k = \min\left(\text{baseDelayMs} \cdot \text{factor}^{\,k-1},\; \text{maxDelayMs}\right) \quad \text{for retry } k = 1, 2, \dots
$$

**Returns:** `Task<TimeSpan?>` — `null` once `failure.RetryNumber >= MaxAttempts`.

**Exceptions:** none thrown. The engine catches a policy that throws and treats it as "no more retries".

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
```

**Verified behavior** (reproduced against the shipped library with `maxAttempts: 3, baseDelayMs: 1`):

```text
[8] retry: status=Completed data=ok drives=3 attempt=1 outcome=Completed
[8] retry logs: 01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
```

The node threw twice and succeeded on the third drive; `Attempt` stayed `1` because a retry is not a pass over the graph.

**Notes:**

- Waits are pure delays: the engine hands the policy a node failure and it answers with a `TimeSpan`, so there is nothing here that inspects the exception. A host that wants "retry a timeout but not a validation error" writes its own — the decision is one method.
- `maxAttempts == 1` means "no retries": the first failure's `RetryNumber` is already `1`, so the policy stops immediately.
