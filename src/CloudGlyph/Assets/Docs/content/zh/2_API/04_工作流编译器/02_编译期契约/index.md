# 编译期契约

路由器声明自己的分支；编译器会问两次，一次要结构，一次要键。节点也可以选择接收编译身份通知，但权威副本在图里。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## ICompileTimeRouter

**签名：** `interface ICompileTimeRouter`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `GetRouteTable()` | `Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>>` | 分支表：键 → 下游节点；一个键可扇出到多个。 |
| `ResolveRouteKey(object? payload)` | `Task<object?>` | 返回当前载荷对应的键；编译期以 `null` 调用。 |

编译期从 `ResolveRouteKey(null)` 返回 `null` 意为「此刻无法决定」，该分支为动态并保留全部选项。返回键则使分支静态，并把该值锁为 `BranchSegment.CompileKey`。运行期动态分支会用会话再次调用 `ResolveRouteKey(context)`。

节点列表为空的选项是终止选项：运行期选择它会结束运行。

## RouterCompileMode

**签名：** `enum RouterCompileMode`

| 值 | 含义 |
| --- | --- |
| `Static` | `GetRouteTable` 只返回选中分支；编译图就是那条单一路径。 |
| `Dynamic` | `GetRouteTable` 返回全部分支；由运行期决定走哪条。 |

`RouterCompileMode` 是路由器回答两次调用时可采用的约定；编译器从不读取该枚举。

## ICompileContext

**签名：** `interface ICompileContext : IAccessContext`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Order` | `int` | 编译期固定执行顺序；`-1` 为绝对停止。 |
| `ChainIndex` | `int` | 线性段内索引。 |
| `Offset` | `int` | 子图入口偏移。 |
| `InputNodes` | `IReadOnlyList<INodeComponent>?` | 汇合输入；链式与单输入节点为 null。 |

继承自 `IAccessContext`：`Data`（编译期为 null）、`Sender`、`Receiver`、`IsCompilePhase`（`true`）。

## CompileContext

**签名：** `sealed partial class CompileContext : ICompileContext`

属性：`IsCompilePhase`（`true`）、`Data`（`null`）、`Sender`（`ISlotComponent?`）、`Receiver`（`ISlotComponent?`）、`InputNodes`、`Order`（默认 `-1`）、`ChainIndex`（默认 `-1`）、`Offset`（默认 `0`）。

编译器有两种用法：

- **边校验** —— 填入 `Sender` 与 `Receiver` 的 `CompileContext` 传给 `INodeHelper.AccessAsync`，每条出边一次。返回 `false` 会丢弃该边。
- **身份通知** —— 分配节点身份后，编译器把副本传给 `ICompileTimeAware`。

两种情况下载荷都是 null：编译期检测是静态的。

## ICompileTimeAware

**签名：** `interface ICompileTimeAware`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `AttachCompileTimeContext(ICompileContext context)` | `void` | 每次到达该节点的编译接收一次快照。 |
| `CompileContext` | `ICompileContext?` | 最近收到的快照，或 null。 |

引擎从不读回这份副本。权威身份是 `CompiledGraph.TryGetCompileInfo`；什么都没实现的节点仍参与汇合、重定向跳过与状态码。`AttachCompileTimeContext` 抛出的异常会被吞掉，不会让编译失败。它适合显示类用途，例如编译徽标。

## 示例

```csharp
[WorkflowBuilder.Node<NodeHelper>]
public partial class RouterNode : ICompileTimeRouter, ICompileTimeAware
{
    public RouterNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotEnumerator<SlotViewModel> OutputSlots { get; set; }

    public Dictionary<object, IReadOnlyList<INodeComponent>> Routes { get; } = [];
    public object? Selection { get; set; } = "A";

    public Task<IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>>> GetRouteTable()
    {
        IReadOnlyDictionary<object, IReadOnlyList<INodeComponent>> table =
            Routes.ToDictionary(kv => kv.Key, kv => kv.Value);
        return Task.FromResult(table);
    }

    public Task<object?> ResolveRouteKey(object? payload)
        => Task.FromResult(payload is null ? null : Selection);   // 编译期为动态

    public ICompileContext? CompileContext { get; private set; }

    public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
}
```
