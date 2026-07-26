# 数据流 — 工作流系统

## 1. 节点工作执行流程

当节点的 `WorkCommand` 被触发时，执行以下序列：

```mermaid
sequenceDiagram
	participant T as TreeViewModel
	participant N as NodeViewModel
	participant NH as NodeHelper
	participant Cmd as WorkCommand
	participant S as Slot System
	participant SN as 相邻节点

	Note over T,SN: 步骤 1：工作执行
	T->>N: WorkCommand.Execute(parameter)
	N->>Cmd: 入队（如果受信号量限制）
	Cmd-->>T: Enqueued 事件
	Cmd->>Cmd: 等待信号量
	Cmd-->>T: Dequeued 事件
	Cmd->>NH: WorkAsync(parameter, ct)
	NH->>NH: 业务逻辑
	NH-->>Cmd: Task 完成
	Cmd-->>T: Exited 事件

	Note over T,SN: 步骤 2：广播（如果配置）
	T->>N: BroadcastCommand.Execute(result)
	N->>S: 对每个有目标的输出槽位...
	S->>SN: 转发数据到连接节点
	SN->>SN: 执行 WorkCommand（递归）
```

## 2. 连接建立流程

```mermaid
sequenceDiagram
	participant T as TreeViewModel
	participant S1 as 源槽位
	participant S2 as 目标槽位
	participant TH as TreeHelper

	Note over T,TH: 阶段 1：虚拟连接
	T->>T: SendConnectionCommand.Execute(sourceSlot)
	T->>TH: SendConnection(slot)
	TH->>T: 设置带发送方的 VirtualLink
	T->>S1: 标记槽位为连接中

	Note over T,TH: 阶段 2：完成连接
	T->>T: ReceiveConnectionCommand.Execute(targetSlot)
	T->>TH: ReceiveConnection(slot)
	TH->>TH: ValidateConnection(sender, receiver)
	alt 有效连接
		TH->>TH: CreateLink(sender, receiver)
		TH->>T: 添加 Link 到 Links 集合
		TH->>S1: 将 target 添加到 Targets
		TH->>S2: 将 source 添加到 Sources
		TH->>TH: ResetVirtualLink()
	else 无效连接
		TH->>TH: ResetVirtualLink()
		Note over T: 连接被拒绝
	end
```

## 3. 空间查询流程（视口裁剪）

```mermaid
sequenceDiagram
	participant View as UI ScrollViewer
	participant Tree as TreeViewModel
	participant TH as TreeHelper
	participant SM as WorkflowSpatialManager
	participant Grid as SpatialGridHashMap
	participant Items as VisibleItems

	Note over View,Items: 滚动 / 缩放时
	View->>TH: 视口变化
	TH->>SM: Query(viewport)
	SM->>Grid: Query(viewport)
	Grid-->>SM: 相交的节点 + 节点对
	SM-->>TH: 结果集
	TH->>Items: 替换 VisibleItems
	Items-->>View: UI 回收视图
```

## 4. 撤销/重做流程

```mermaid
sequenceDiagram
	participant User
	participant Tree as TreeViewModel
	participant Stack as 撤销栈
	participant Pair as WorkflowActionPair

	User->>Tree: SubmitCommand.Execute(pair)
	Tree->>Pair: pair.Do()
	Tree->>Stack: Push(pair)

	Note over User,Stack: 稍后...
	User->>Tree: UndoCommand.Execute(null)
	Tree->>Stack: Pop → pair
	Tree->>Pair: pair.Undo()
	Tree->>RedoStack: Push(pair)

	Note over User,Stack: 或...
	User->>Tree: RedoCommand.Execute(null)
	Tree->>RedoStack: Pop → pair
	Tree->>Pair: pair.Do()
	Tree->>Stack: Push(pair)
```

## 5. 序列化流程

```mermaid
flowchart LR
	A[TreeViewModel] -->|Serialize| B[JSON]
	B -->|Deserialize| C[TreeViewModel copy]
	C -->|UpdateCommand.Execute| D[Layout restored]
	D -->|WorkflowBehaviors.Refresh| E[UI re-renders]
```

`VeloxDev.MVVM.Serialization` 命名空间提供 `Serialize()` 和 `Deserialize<T>()` 扩展方法。序列化保留完整的对象图：节点、槽位、连接线、布局状态和自定义数据属性。
