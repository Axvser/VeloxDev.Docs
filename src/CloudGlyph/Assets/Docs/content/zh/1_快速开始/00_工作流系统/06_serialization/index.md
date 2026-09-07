# 工作流系统 — 序列化

把整棵树（节点、槽位、连接、布局、自定义 `[VeloxProperty]` 数据）持久化为 JSON，再从 JSON 重建。这依赖扩展包里的 `VeloxDev.MVVM.Serialization.ComponentModelEx`（`VeloxDev.Core.Extension`），本页先补上 using 再沿用前几页的对象。

```csharp
using VeloxDev.MVVM.Serialization;

var json = tree.Serialize();
var copy = json.Deserialize<CalcTree>();
Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count} " +
                  $"origin={copy.Layout.OriginSize.Width}x{copy.Layout.OriginSize.Height} jsonLen={json.Length}");
```

要点：

- `Serialize<T>()` 用 Newtonsoft 序列化，**只写公开可写属性**（生成器的 `RuntimeId` 等计算属性被排除）。
- 反序列化走无参构造（构造里已 `InitializeWorkflow` 装好 Helper / 默认槽位），再按 JSON 属性重建对象图；`CompileContext` 这类私 setter 的编译身份不落盘，下次编译时重新注入。
- 还有 `SerializeAsync` / `DeserializeAsync` / `TryDeserialize<T>` / `SerializationOptions`（缩进、类型名处理等）等重载。

**预期结果：** `copy.Nodes.Count == 3`、`copy.Links.Count == 2`、`copy.Layout.OriginSize` 为 `1200x800`；`json` 非空。

重建后的副本应能直接重新编译运行 —— 这是最有力的往返验证：

```csharp
var copySource = copy.Nodes.OfType<CalcNode>().First(n => n.Title == "Source");
var copyGraphs = await new CompilerViewModel().CompileAsync(copySource, CompileRole.Root);
var copyCtx = new RuntimeContext { Data = 2.0 };
await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);
Console.WriteLine($"copy run status={copyCtx.Status} data={copyCtx.Data}");
```

**预期结果（真实运行输出）：**

```text
copy Nodes=3 Links=2 origin=1200x800 jsonLen=7366
  [Source] kind=double order=0 result=4
  [Report] kind=pass order=1 result=4
  [Discard] kind=pass order=2 result=4
copy run status=Completed data=4
```

`jsonLen` 具体数值取决于程序集与类型版本；关键是 **副本与原图行为一致**（同样 3 节点 2 连线、同样的运行结果）。

> 持久化保存/加载在 WPF Demo 里对应 `TreeViewModel.Save`（`this.Serialize()` 写文件），会话重建见 `WorkflowDemoSession.FromTree`（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`）。

## 下一步

所有步骤都验证过了，进入 [07 验证与完整代码](../07_complete-code/index.md)：对照 Demo/测试，并把上面的类与步骤拼成单一可运行程序。
