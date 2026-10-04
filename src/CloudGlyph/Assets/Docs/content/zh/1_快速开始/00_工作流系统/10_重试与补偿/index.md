# Workflow System — 重试失败的节点与补偿一次糟糕的运行

两条关于失败的能力：重试策略给**抛出异常**的节点再一次机会，补偿器则被告知一次收尾不佳的运行已经做了什么，好让宿主撤销它。

## 1. 加一个前两次必失败的节点

在 `WorkflowQuickStart` 项目里创建 `FlakyNode.cs`：

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

**预期结果：** 编译通过。没有重试策略时，这个节点第一次抛出就会结束整轮。

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

三次驱动、`data=ok`，而 `attempt=1`：**重试不是一趟过图**。另外注意没有 `[Error]` 行 —— 将要被重试的一次尝试还不是错误。

**说明：** 只有**抛出的异常**会被重试。调用 `Error` / `ErrorAsync` 的节点是在做刻意的重定向请求 —— 那是它自己要的控制流，不是值得再试一次的失败 —— 所以不会询问任何策略。节点会从**同一个输入**重新驱动。重试等待期间取消会结束整轮。永远返回等待时长的策略会无限重试：运行没有别的上限，用 `NodeFailure.RetryNumber` 自己收口。

## 3. 加一个永远失败的节点

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

**预期结果：** 编译仍通过。

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
catch (InvalidOperationException) { }        // 节点自己的异常会冒到调用方

Console.WriteLine($"{context.Status} {context.Outcome} currentOrder={context.CurrentOrder} reversed=[{string.Join(", ", compensated)}]");
```

**预期结果：**

```text
Stopped Failed currentOrder=-1 reversed=[BoomNode]
```

运行以 `Stopped` / `Failed` 收尾，状态码掉到 `-1`（绝对停止），补偿器拿到了失败之前成功过的那个节点 —— 最近的在前。这里只有一个。

**说明：** **引擎什么都不回滚，而且做不到。** 一个节点的副作用是它自己的 —— 它写下的属性、它启动的进程、它留下的文件 —— 只有宿主知道哪些可逆。树的撤销栈不是替代品：它只记模型结构变更，是一条没有运行边界的扁平栈，而且不保证链条完整。

补偿**只在**结局是 `Failed` 或 `Cancelled` 时被调用 —— 完成的运行不补偿任何东西。抛异常的补偿会被记日志（`[Compensation] …`），剩下的节点照旧清理，因为最初那次失败仍是头条。被重定向驱动两次的节点只出现**一次**，位置是它最近一次成功。

## 5. 真实仓库里它在哪

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 的 `ConfigureRun`：

```csharp
// publish 节点的第一次投递是刻意失败的；这就是让它过的那一环。
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
context.Compensation = new DelegateExecutionCompensation(
    c => Controller.RuntimeContext?.Log($"[Compensation] undo {NameOf(c.Node)} (attempt {c.Order})"));
```

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionRetryTests.cs`（含 `ANodeThatAsksForARedirect_IsNotRetried` 与 `CancellingDuringTheRetryWait_EndsTheRun`）与 `ExecutionCompensationTests.cs`。

下一步见 `11_检查点与日志`。
