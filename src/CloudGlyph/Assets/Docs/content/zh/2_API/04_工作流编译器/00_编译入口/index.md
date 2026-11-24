# 编译入口

一个方法编译一张图，一个枚举决定遍历方向。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## CompileRole

**签名：** `enum CompileRole`

| 值 | 含义 |
| --- | --- |
| `Root` | 节点是根起点；编译沿 `Targets` 下游可达的子图。 |
| `Terminal` | 节点是结果终点；沿 `Sources` 收集其祖先锥，只编译计算它所需的部分。 |

## CompilerViewModel

**签名：** `sealed partial class CompilerViewModel`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Graphs` | `ObservableCollection<CompiledGraph>` | 最近一次编译产出的图。 |
| `CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default)` | `Task<IReadOnlyList<CompiledGraph>>` | 唯一入口；`T : IWorkflowComponent`。 |

### CompileAsync

**签名：** `Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default) where T : IWorkflowComponent`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `component` | `T` | 必须是 `INodeComponent`；它扮演 `role`。 |
| `role` | `CompileRole` | `Root` 或 `Terminal`。 |
| `ct` | `CancellationToken` | 在节点与边之间取消。 |

**返回：** `IReadOnlyList<CompiledGraph>` —— 当前实现总是返回一张图。`Graphs` 被清空并重新填入它。

**异常：**

| 异常 | 条件 |
| --- | --- |
| `ArgumentException` | `component` 不是 `INodeComponent`。 |
| `ArgumentOutOfRangeException` | `role` 不是已定义值。 |
| `InvalidOperationException` | Terminal 模式：路由器有多条分支可达目标，或锥的独立生产者没有汇入同一共同汇合点。 |

调用之所以异步，是因为路由器的 `GetRouteTable`/`ResolveRouteKey` 与每条边的 `AccessAsync` 都是异步的。`Root` 从 `component` 开始；`Terminal` 先用反向 BFS 构建祖先锥，再编译锥自身的入口前沿。

## 分解规则

- 单输入单输出的线性段成为 `ChainSegment`。
- `ICompileTimeRouter` 成为 `BranchSegment`。静态键会剪掉未选分支；动态键保留全部选项。
- 某个路由键有多个目标，或普通节点有多个有效目标，成为 `ParallelSegment`。所有分支出口共同指向的节点成为汇合点，也是下一段链的起点。
- 已访问节点不重复编译；编译图是无环的。
- 每条边在编译期都会用 `INodeHelper.AccessAsync` 检查。被拒绝的边按未连接跳过，与运行期行为一致。
- 静态模式下，未选分支的节点会被访问并赋 `Order = -1`（绝对停止态），且不出现在任何段里。
- `AccessAsync` 未接受的边不会出现在图中。

重定向不属于编译图；它是运行期契约（`IRedirectable`）。

## 示例

```csharp
var compiler = new CompilerViewModel();
var root = await compiler.CompileAsync(startNode, CompileRole.Root);
Console.WriteLine(root.Count);                 // 1
Console.WriteLine(compiler.Graphs.Count);      // 1

var cone = await compiler.CompileAsync(targetNode, CompileRole.Terminal);
Console.WriteLine(cone[0].Entries.Count);
```
