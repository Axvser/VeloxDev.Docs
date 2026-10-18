# 工作流系统 — 重试失败节点并补偿坏运行

两项关于失败的能力：重试策略给**抛过异常**的节点再一次机会；补偿器则被告知一次糟糕结束的运行已经做过什么，好让宿主撤销它。

## 1. 添加一个前两次失败的节点

在 `WorkflowQuickStart` 工程中创建 `FlakyNode.cs`：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

[WorkflowBuilder.Node<FlakyHelper>(workSemaphore: 1)]
public partial class FlakyNode : ICompileTimeAware
{
    public FlakyNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class FlakyHelper : NodeHelper<FlakyNode>
{
    public static int Attempts;

    public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
    {
        Attempts++;
        if (Attempts < 3) throw new InvalidOperationException($"flaky #{Attempts}");
        return Task.FromResult<object?>("ok");
    }
}
```

**预期结果：** 工程可编译。没有重试策略时，这个节点第一次抛异常就会结束运行。

## 2. 挂上重试策略

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var tree = new QuickTree();
var helper = tree.GetHelper();
var flaky = new FlakyNode { Anchor = new Anchor(0, 0, 0) };
helper.CreateNode(flaky);

var graph = (await new CompilerViewModel().CompileAsync(
    flaky, CompileRole.Root, CancellationToken.None))[0];

var context = new RuntimeContext
{
    RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 1),
};

await new RuntimeEngine().RunAsync(graph, context, CancellationToken.None);
Console.WriteLine($"{context.Status} data={context.Data} drives={FlakyHelper.Attempts} attempt={context.Attempt}");
Console.WriteLine(string.Join(" | ", context.Logs));
```

**预期结果：**

```text
Completed data=ok drives=3 attempt=1
01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
```

三次驱动、`data=ok`、`attempt=1`：**重试不是对图的一趟新遍历。** 另外注意没有 `[Error]` 行 —— 一次即将重试的尝试还不算错误。

**说明：** 只有**抛出的异常**会被重试。调用 `Error` / `ErrorAsync` 的节点是在发出刻意的重定向请求 —— 它自己要求的控制流，不是需要再试一次的失败 —— 因此不会询问策略。节点会从**同一输入**重新驱动。重试等待期间取消会结束运行。总是返回延迟的策略会永远重试：运行没有其他上限，请用 `NodeFailure.RetryNumber` 终止。

## 3. 添加一个总是失败的节点

`BoomNode.cs`：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

[WorkflowBuilder.Node<BoomHelper>(workSemaphore: 1)]
public partial class BoomNode : ICompileTimeAware
{
    public BoomNode() => InitializeWorkflow();

    [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
    [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}

public class BoomHelper : NodeHelper<BoomNode>
{
    public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        => throw new InvalidOperationException("boom");
}
```

**预期结果：** 工程仍可编译。

## 4. 挂上补偿器

```csharp
var compensated = new List<string>();
var boom = new BoomNode { Anchor = new Anchor(0, 0, 0) };
var boomTree = new QuickTree();
boomTree.GetHelper().CreateNode(boom);
var boomGraph = (await new CompilerViewModel().CompileAsync(
    boom, CompileRole.Root, CancellationToken.None))[0];

var context = new RuntimeContext
{
    Compensation = new DelegateExecutionCompensation(c => compensated.Add(c.Node.GetType().Name)),
};

try
{
    await new RuntimeEngine().RunAsync(boomGraph, context, CancellationToken.None);
}
catch (InvalidOperationException) { }        // the node's own exception surfaces to the caller

Console.WriteLine($"{context.Status} {context.Outcome} currentOrder={context.CurrentOrder} reversed=[{string.Join(", ", compensated)}]");
```

**预期结果：**

```text
Stopped Failed currentOrder=-1 reversed=[BoomNode]
```

运行以 `Stopped` / `Failed` 结束，状态码降到 `-1`（绝对停止），补偿器收到失败前已成功的节点 —— 最近的在最前。这里只有一个。

**说明：** **引擎不回滚任何东西，也无法回滚。** 节点的副作用是它自己的 —— 写过的属性、启动的进程、留下的文件 —— 只有宿主知道哪些可逆。树的撤销栈不是替代品：它只记录模型结构变更，是一个没有运行边界的扁平栈，也不保证链能走完。

只有结果为 `Failed` 或 `Cancelled` 时才调用补偿 —— 完成的运行不补偿任何东西。补偿器抛异常会被记录（`[Compensation] …`），其余节点仍会继续，因为原始失败仍是头条。被重定向驱动两次的节点**只出现一次**，取最近一次成功的位置。

## 5. 真实仓库中的位置

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`，`ConfigureRun`：

```csharp
// The publish node's first delivery fails on purpose; this is what gets it through.
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
context.Compensation = new DelegateExecutionCompensation(
    c => Controller.RuntimeContext?.Log($"[Compensation] undo {NameOf(c.Node)} (attempt {c.Order})"));
```

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionRetryTests.cs`（含 `ANodeThatAsksForARedirect_IsNotRetried` 与 `CancellingDuringTheRetryWait_EndsTheRun`）及 `ExecutionCompensationTests.cs`。

前往「检查点与日志」。
