# 工作流编译器

`CompileAsync` 遍历一次可达子图，把它分解为链、分支与并行段。已访问集合使遍历对图线性；超线性项来自在每个决策点重扫节点插槽，以及反向（祖先锥）模式——那里用线性扫描对前驱列表去重。

记号：$V$ 个节点，$E$ 条插槽边，单节点最大度 $d$，路由器返回的 $K$ 个路由键，生成的 $S$ 个段，分支嵌套深度 $D$，祖先锥 $V_c$、$E_c$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `CompileAsync`，Root | 最坏 $O(V + E d)$；度有界时 $O(V + E)$ | $O(V + E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:38` |
| 链式线性遍历 | $O(V)$ | 访问集 $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:69` |
| 路由器扇出 | 每个路由器 $O(K \cdot \text{目标数})$ | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:103` |
| 普通节点扇出 | $O(\text{合法目标数})$ + 每个目标一次递归编译 | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:223` |
| 静态剪枝 BFS | 被跳过子图 $O(V_s + E_s)$ | $O(V_s)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:308` |
| 边校验 | $O(E)$ 次 await | $O(E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:443` |
| 反向祖先锥 | 最坏 $O(V_c + E_c d)$ | $O(V_c + E_c)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs:34` |
| 大纲扁平化 | $O(S + N)$ | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/Model/CompiledOutline.cs:35` |

## 访问集让遍历保持线性

链用循环而非递归跟进，所以很长的线性图不会增长栈。在上一轮已编译过的节点会终止遍历：

```csharp
while (node != null)
{
    if (!ReferenceEquals(node, start) && !resumedAfterBranch && HasMultipleInputs(node, state.Cone))
        break;
    if (!state.Visited.Add(node))
        break;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:69-79`

递归只发生在分支与扇出目标上，所以栈深为 $O(D)$ 而非 $O(V)$。每个节点只编译一次，得到：

$$
T_{\text{compile}}(V,E) = O(V + E)
$$

前提是节点携带的插槽数有界。`HasMultipleInputs`、`SingleTarget` 与目标枚举各自重扫该节点自己的插槽，当单节点端口很多时引入 $E d$ 因子。

## 额外因子的来源

路由键与分支目标在嵌套循环中配对，每个目标启动一次递归编译：

```csharp
foreach (var kv in routeTable)
{
    if (kv.Value.Count == 1)
        var sub = await CompileGraphAsync(target, state, ct);
    ...
    foreach (var t in kv.Value)
        var sub = await CompileGraphAsync(t, state, ct);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs:103-139`

这里没有并发：每次路由器调用与每次 `AccessAsync` 规则检查都按顺序 await。"并行"段的构造是顺序工作，它只是*描述*运行期扇出，因此墙钟时间等于总工作量。

## 反向上界最弱

祖先锥模式构建前驱列表，并用线性 `Any` 扫描对每个前驱去重：

```csharp
foreach (var source in slot!.Sources ?? [])
{
    ...
    if (!list.Any(p => ReferenceEquals(p, sender)))
        ...
    if (cone.Add(sender))
        queue.Enqueue(sender);
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs:50-67`

对扇入为 $F$ 的节点，每个汇合点的去重是 $O(F^2)$。因此稀疏情形下反向上界为 $O(V_c + E_c d)$，稠密扇入时为 $O(\sum F^2)$。

```plot
{
  "title": "编译工作量：稀疏图与稠密扇入",
  "grid": true,
  "xAxis": { "domain": [0, 80] },
  "yAxis": { "domain": [0, 6400] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(V + E)，访问式遍历" },
    { "fn": "x*log(x+1)", "color": "#a78bfa", "title": "路由表 + 目标扫描" },
    { "fn": "x*x", "color": "#f472b6", "title": "反向去重，稠密扇入" }
  ]
}
```

## 内存

编译状态持有访问集 $O(V)$、绑定表 $O(V)$（结果图会保留它）、汇合输入列表 $O(\text{汇合数})$，以及段/选项/分支列表 $O(S + K \cdot \text{目标数})$。大纲是另一个 $O(S)$ 列表。递归栈为 $O(D)$；线性链是迭代的，不按链长消耗栈。
