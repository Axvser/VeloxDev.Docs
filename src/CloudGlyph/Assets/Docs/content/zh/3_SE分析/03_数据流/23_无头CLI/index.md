# 无头 CLI

本页追踪 `VeloxDev.Cli` 的两个动词：`run`（一次性无头执行）与 `mcp`（围绕一份归档长期运行的 stdio MCP 服务器）。也追踪两者共享的归档、插件与 worker 路径。

CLI 没有 demo；其证据是测试套件与源码。

## 入口与解析

入口是 async 顶层程序。它解析一次、按 `Mode` 分派，并把用法错误映射到退出码 2、运行时错误映射到退出码 1。

Source: `Src/Cli/VeloxDev.Cli/Program.cs:12-41`

```csharp
try
{
    var options = CliOptions.Parse(args);

    if (options.ShowHelp)
    {
        Console.Out.WriteLine(CliOptions.Usage);
        return 0;
    }

    if (options.Mode == "run")
        return await RunOnceAsync(options);

    await McpHost.RunAsync(options);
    return 0;
}
catch (CliUsageException ex) { /* usage + exit 2 */ }
catch (Exception ex) { /* one-line error + exit 1 */ }
```

`CliOptions.Parse` 只接受两个动词。它在读取任何选项之前拒绝未知动词，并在循环之后校验必需的 `--archive`（`run` 还要 `--start`）。

Source: `Src/Cli/VeloxDev.Cli/CliOptions.cs:95-104`, `206-213`

```csharp
public static CliOptions Parse(string[] args)
{
    if (args.Length == 0) return new CliOptions { ShowHelp = true };
    if (args[0] is "--help" or "-h" or "help") return new CliOptions { ShowHelp = true };

    var mode = args[0];
    if (mode is not ("mcp" or "run"))
        throw new CliUsageException($"Unknown command '{mode}'. Expected 'mcp' or 'run'.");
    // ... option loop ...
    if (string.IsNullOrWhiteSpace(options.Archive))
        throw new CliUsageException("--archive is required.");
    if (mode == "run" && options.StartNode is null)
        throw new CliUsageException("--start is required for 'run'.");
    return options;
}
```

## `run` 动词

`RunOnceAsync` 以强制执行模式创建会话，向 toolkit 索取执行工具，调用它，并可选地写出运行后的树。

Source: `Src/Cli/VeloxDev.Cli/Program.cs:47-91`

```csharp
static async Task<int> RunOnceAsync(CliOptions options)
{
    await using var session = WorkflowSession.Create(options, forceExecution: true);

    var toolName = options.NodeResult ? "GetNodeResult" : "RunCompiledWorkflow";
    var tool = session.Toolkit.CreateTools(WorkflowToolCategory.Execution)
        .OfType<AIFunction>()
        .FirstOrDefault(t => string.Equals(t.Name, toolName, StringComparison.Ordinal))
        ?? throw new InvalidOperationException($"{toolName} is not available on this toolkit.");

    var arguments = new AIFunctionArguments
    {
        [options.NodeResult ? "nodeIndex" : "startNodeIndex"] = options.StartNode!.Value,
    };
    // ... seed, timeout ...

    var result = await tool.InvokeAsync(arguments).ConfigureAwait(false);
    // ... optional --output-tree write, guarded by WorkspaceRule.Ensure ...
    Console.Out.WriteLine(text);
    return IsOk(text) && outputWritten ? 0 : 1;
}
```

会话创建是两个动词共享的路径：归一化工作区、加载归档与清单、加载每个依赖程序集、反序列化树，然后配置作用域。

Source: `Src/Cli/VeloxDev.Cli/WorkflowSession.cs:147-179`, `203-262`

```csharp
var workspace = WorkspaceRule.Normalize(options.Workspace);
WorkspaceRule.Ensure(workspace, options.Archive, "Archive");
WorkspaceRule.Ensure(workspace, options.Manifest, "Manifest");
// ... checkpoint, log, assemblies ...

var plugins = new PluginLoader();
plugins.StrictVersions = options.StrictPluginVersions;
plugins.CopyAssemblies = !options.NoAssemblyCopy;
// ...
```

```csharp
var archive = WorkflowArchive.Load(request.Path, request.Manifest);
foreach (var assembly in archive.Assemblies)
{
    WorkspaceRule.Ensure(workspace, assembly, "Dependency assembly");
    plugins.Load(assembly);
}
// ...
tree = VeloxJsonSerializer.Deserialize(archive.Json, rootType) as ITreeComponent
    ?? throw new InvalidDataException(...);

var scope = new WorkflowAgentScope(tree);
if (execution) scope.WithAllowNodeExecution(true);
scope.WithAutoDiscovery(AgentLanguages.English);
```

```plantuml
@startuml
!theme plain

actor User as User
participant "Program" as Program
participant "CliOptions" as Options
participant "WorkflowSession" as Session
participant "WorkflowArchive" as Archive
participant "PluginLoader" as Plugins
participant "WorkflowAgentToolkit" as Toolkit
participant "RuntimeEngine" as Engine

User -> Program: veloxdev run --archive g.json --start N
Program -> Options: Parse(args)
Options --> Program: Mode=run, paths
Program -> Session: Create(options, forceExecution: true)
Session -> Plugins: new PluginLoader()
Session -> Archive: Load(path, manifest)
Archive --> Session: Json + assemblies + root type
loop each dependency assembly
    Session -> Plugins: Load(path)
end
Session -> Session: VeloxJsonSerializer.Deserialize(json, rootType)
Session -> Session: new WorkflowAgentScope(tree)
Session -> Session: WithAllowNodeExecution(true)
Session -> Session: WithAutoDiscovery(English)
Session --> Program: session
Program -> Toolkit: CreateTools(Execution)
Toolkit --> Program: RunCompiledWorkflow tool
Program -> Engine: tool.InvokeAsync({ startNodeIndex })
Engine --> Program: { status, outcome, data, logs }
Program -> Program: WorkspaceRule.Ensure(outputTree)
Program --> User: result JSON + exit code
@enduml
```

`run` 动词即使归档清单不允许也强制执行，因为用户启动这个进程就是为了运行。`mcp` 动词不会：那里只有 `--allow-execution` 或清单才启用执行。

Source: `Src/Cli/VeloxDev.Cli/WorkflowSession.cs:233-236`

```csharp
var execution = executionEnabled ?? (options.AllowExecution || archive.ManifestAllowsExecution);
var inProcess = inProcessExecution ?? options.InProcessExecution;
var scope = new WorkflowAgentScope(tree);
if (execution) scope.WithAllowNodeExecution(true);
```

## `mcp` 动词

`McpHost.RunAsync` 构建 `WorkflowSessionHost`，然后通过 stdio 发布工具、资源与提示。日志被导到 stderr，因为 stdout 是 JSON-RPC 流。

Source: `Src/Cli/VeloxDev.Cli/McpHost.cs:14-49`

```csharp
await using var host = WorkflowSessionHost.Create(options);
await using var jobs = new WorkerJobRegistry();
var session = host.Current;

var builder = Host.CreateApplicationBuilder();
builder.Logging.ClearProviders();
builder.Logging.SetMinimumLevel(LogLevel.Warning);
builder.Logging.AddConsole(console => console.LogToStandardErrorThreshold = LogLevel.Trace);

var tools = session.CreateMcpTools(host);
var mcp = builder.Services
    .AddMcpServer(server => { server.ServerInfo = ...; server.ServerInstructions = session.BuildInstructions(); })
    .WithStdioServerTransport()
    .WithTools(tools)
    .WithTools(new ArchiveTools(host))
    .WithResources(new SessionResources(host))
    .WithPrompts(new SessionPrompts(host));

if (session.ExecutionEnabled) mcp.WithTools(new RedirectTools(host));
if (session.ExecutionEnabled && !session.InProcessExecution)
    mcp.WithTools(new ExecutionTools(host, jobs));

await builder.Build().RunAsync(cancellationToken).ConfigureAwait(false);
```

每个原生图工具都是绑定到 host 而非启动会话的稳定代理。这正是 `LoadArchive` 能替换会话而无需重新注册工具的原因：代理在调用时解析当前会话。

Source: `Src/Cli/VeloxDev.Cli/WorkflowSession.cs:273-287`

```csharp
public IReadOnlyList<McpServerTool> CreateMcpTools(WorkflowSessionHost host)
{
    var tools = new List<McpServerTool>();
    foreach (var (function, mutating, executable) in BuildExposedFunctions())
    {
        tools.Add(McpServerTool.Create(new SessionBoundAIFunction(host, function), new McpServerToolCreateOptions
        {
            ReadOnly = !mutating && !executable,
            Destructive = mutating || executable,
            OpenWorld = executable,
        }));
    }
    return tools;
}
```

```plantuml
@startuml
!theme plain

actor Client as Client
participant "McpHost" as Host
participant "WorkflowSessionHost" as SessionHost
participant "ArchiveTools" as ArchiveTools
participant "ExecutionTools" as ExecTools
participant "WorkerJobRegistry" as Jobs

Client -> Host: stdio JSON-RPC initialize
Host -> SessionHost: Create(options)
SessionHost -> SessionHost: WorkflowSession.Create(...)
Host -> Host: CreateMcpTools(host) -> SessionBoundAIFunction proxies
Host --> Client: tools/list (native graph tools + archive + execution)
Client -> ArchiveTools: LoadArchive(path)
ArchiveTools -> SessionHost: ReloadAsync(request, redirect)
SessionHost -> SessionHost: build next session, swap, dispose old when unleased
ArchiveTools --> Client: session description
Client -> ExecTools: RunCompiledWorkflow(startNodeIndex)
ExecTools -> Jobs: registry or WorkerRunner
ExecTools --> Client: run result JSON
@enduml
```

## 归档重载

`LoadArchive` 在两种配置下被拒，原因都是正确性而非便利：进程内执行时运行句柄属于被替换的会话；`--single-archive` 时进程承诺运行时 ID 稳定。

Source: `Src/Cli/VeloxDev.Cli/WorkflowSessionHost.cs:254-296`

```csharp
if (inProcess)
    throw new InvalidOperationException(
        "LoadArchive is unavailable with --in-process-execution: the run handles belong to the session being replaced. ...");

if (_options.SingleArchive)
    throw new InvalidOperationException(
        "LoadArchive is unavailable under --single-archive: this process serves one document for its lifetime ...");

// Build first. A failed load leaves the current session untouched.
var next = WorkflowSession.Create(_options, request, _plugins, _logWriter, _logFile, redirectOnError, ...);

WorkflowSession? old;
lock (_gate)
{
    old = _current;
    _current = next;
    if (_leases > 0) _retired = old;
    else old = null;
}

if (old is not null) await old.DisposeAsync().ConfigureAwait(false);
```

租约把会话钉住一次工具调用。若重载落在调用在途时，旧会话被退休，并在最后一个租约释放时处置。

## 隔离 worker

隔离模式下执行是一个子 `dotnet` 进程。父进程把当前树序列化到临时快照（含根 `$type`，因此子进程不需要 `--root-type`），以 `run` 模式启动 CLI，再读回结果与运行后状态文件。

Source: `Src/Cli/VeloxDev.Cli/WorkerRunner.cs:27-55`, `57-83`

```csharp
var snapshot = Path.Combine(directory, runId + ".json");
var state = Path.Combine(directory, runId + ".state.json");

try
{
    File.WriteAllText(snapshot, session.Scope.Tree.Serialize());

    var startInfo = BuildStartInfo(snapshot, state, nodeResult, index, seed, timeoutMs);
    return await ExecuteAsync(startInfo, nodeResult, timeoutMs, session.WorkerKillGraceMs, ct).ConfigureAwait(false);
}
finally
{
    try { File.Delete(snapshot); } catch { }
}
```

`WorkerJobRegistry.Start` 是异步形态：它取得租约、注册作业，并在并发槽位下以后台任务运行。取消会取消作业 token；worker 进程在配置的宽限期后被杀。

Source: `Src/Cli/VeloxDev.Cli/WorkerJobRegistry.cs:91-110`, `159-167`

```csharp
public string Start(WorkflowSessionHost host, bool nodeResult, int index, string? seed, int? timeoutMs)
{
    var id = Guid.NewGuid().ToString("N")[..10];
    var lease = host.Acquire();
    var job = new WorkerJob(id, nodeResult, index, lease);
    lock (_gate) { _jobs[id] = job; }
    job.Task = RunAsync(host, job, seed, timeoutMs);
    return id;
}
```

```csharp
private static async Task RunAsync(WorkflowSessionHost host, WorkerJob job, string? seed, int? timeoutMs)
{
    var slots = host.RunSlots;
    try { if (slots is not null) await slots.WaitAsync(job.Cancellation.Token).ConfigureAwait(false); }
    catch (OperationCanceledException) { job.MarkCancelled(); job.Lease.Dispose(); return; }
    // ... run the worker ...
}
```

## 工作区沙箱、重定向与运行 CSV

`WorkspaceRule.Ensure` 是可选的沙箱：设置 `--workspace` 后，进程读写的每个路径都必须解析在其下。它在会话创建时检查一次，并在每次 `SaveArchive` / 输出写入时再检查。

Source: `Src/Cli/VeloxDev.Cli/WorkspaceRule.cs:28-41`

```csharp
public static void Ensure(string? workspace, string? path, string what)
{
    if (workspace is null || string.IsNullOrWhiteSpace(path)) return;

    var full = Path.GetFullPath(path);
    var comparison = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;

    var prefix = workspace + Path.DirectorySeparatorChar;
    if (!full.StartsWith(prefix, comparison))
        throw new InvalidOperationException($"{what} '{full}' is outside the workspace '{workspace}'. ...");
}
```

`RunLogCsv.TryWrite` 尽力而为：执行结果的 `logs` 与 `failures` 变成 `tasks/<task>/runs/<timestamp>_<tool>.csv` 下的行，路径以 `csvFile` 附加。运行不会因为日志写不出而失败。

Source: `Src/Cli/VeloxDev.Cli/RunLogCsv.cs:22-44`, `92-99`

```csharp
public static string? TryWrite(string taskDirectory, string tool, string json)
{
    try
    {
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;
        if (root.ValueKind != JsonValueKind.Object) return null;
        // ... hasLogs / hasFailures ...
        var runs = Path.Combine(taskDirectory, "runs");
        Directory.CreateDirectory(runs);
        var stamp = DateTimeOffset.UtcNow.ToString("yyyyMMdd-HHmmss-fff", CultureInfo.InvariantCulture);
        var path = Path.Combine(runs, $"{stamp}_{Sanitize(tool)}.csv");
        // ... write header and rows ...
        return path;
    }
    catch { return null; }
}
```

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— CLI 发布的 toolkit。
- [智能体安全与预算](../18_智能体安全与预算/index.md) —— 暴露的工具仍要穿过的闸门。
- [MCP 集成](../20_MCP集成/index.md) —— 协议的客户端一侧。
- [平台适配器契约](../24_平台适配器契约/index.md) —— CLI 省略的 GUI 对应物。
