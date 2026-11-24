# 连接规则与预览

只有当框架规则、树助手的 `ValidateConnection` 与释放时的 `Connecting` 否决全部同意，连接才成立。拖拽预览运行同一套框架规则，因此绿色橡皮筋与最终连线不会在这些规则上互相矛盾。

公开面分为规则集与拖拽状态：

- [连接规则](00_连接规则/index.md) — `ConnectionCheck`、`ConnectionRejectReason`、`SlotChannel`、`SlotState`，以及标准的检查/发送/接收/重置操作。
- [连接预览](01_连接预览/index.md) — `WorkflowInput`、`ConnectionPreviewState`、`IConnectionPreviewLink`、预览方法、`ITreeEvents` 与事件参数。

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel();
var b = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

var from = new SlotDefaultViewModel();
var to = new SlotDefaultViewModel();
a.CreateSlotCommand.Execute(from);
b.CreateSlotCommand.Execute(to);

var check = tree.StandardCheckConnection(from, to);
Console.WriteLine(check);   // Valid
```

任务式教程见[连接规则与预览](../../1_快速开始/02_连接规则与预览/index.md)。
