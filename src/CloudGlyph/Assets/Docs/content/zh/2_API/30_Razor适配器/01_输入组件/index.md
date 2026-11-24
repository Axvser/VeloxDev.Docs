# 输入组件

命名空间：`VeloxDev.WorkflowSystem.AttachedBehaviors`。

每个组件把内容包进一个绝对定位元素，并负责一种手势。对应的 JS 初始化器测量并驱动这个元素；组件把按下路由进 Core，再执行得到的命令。

## 类：WorkflowNodeDragBehavior

`public partial class WorkflowNodeDragBehavior : ComponentBase, IAsyncDisposable`

渲染 left/top/z-index 跟随 `INodeComponent.Anchor` 的节点内容，并把指针拖动转成 `MoveCommand`。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Node` | `INodeComponent?` | `null` | 要渲染并移动的节点。 |
| `IsEnabled` | `bool` | `false` | 加载 JS 节点拖动初始化器。 |
| `Style` | `string?` | `null` | 附加到定位包装元素上的额外样式。 |
| `ChildContent` | `RenderFragment?` | `null` | 节点内容。 |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `RequestPressVerdict(double localX, double localY, int button, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`；在节点自己的中继上路由这次按下。 |
| `OnNodeDrag(double dx, double dy)` | `void` | `[JSInvokable]`；以世界位移执行 `MoveCommand`。 |
| `OnNodeDragEnd()` | `void` | `[JSInvokable]`；把包装元素吸附到最终 .NET 锚点。 |
| `DisposeAsync()` | `ValueTask` | 释放节点订阅与 JS 句柄。 |

拖动期间，`Anchor` 变化不会重渲染或重新定位包装元素：位置由 JS 掌管到拖动结束。

### 示例

```razor
<WorkflowNodeDragBehavior Node="node" IsEnabled="true"
                          Style="width:260px;height:180px;">
    <NodeView />
</WorkflowNodeDragBehavior>
```

## 类：WorkflowSlotConnectionBehavior

`public partial class WorkflowSlotConnectionBehavior : ComponentBase, IAsyncDisposable`

包住插槽内容，把连线手势转成 send / set-pointer / receive / reset 命令。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Slot` | `ISlotComponent?` | `null` | 发起并接收连线的插槽。 |
| `Tree` | `ITreeComponent?` | `null` | 拥有连线手势的树。 |
| `IsEnabled` | `bool` | `false` | 加载 JS 插槽连线初始化器。 |
| `Style` | `string?` | `null` | 包装元素样式。 |
| `ChildContent` | `RenderFragment?` | `null` | 插槽内容。 |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `RequestPressVerdict(double localX, double localY, int button, int modifiers, string? targetId)` | `bool` | `[JSInvokable]`；在插槽自己的中继上路由这次按下。 |
| `OnSlotConnectionStart(double worldX, double worldY)` | `void` | `[JSInvokable]`；钉住插槽锚点并执行 `SendConnectionCommand`。 |
| `OnSlotConnectionMove(double worldX, double worldY)` | `void` | `[JSInvokable]`；设置指针并更新预览接收口。 |
| `OnSlotConnectionEnd(string? targetSlotId)` | `void` | `[JSInvokable]`；在目标插槽上接收，或重置虚拟连线。 |
| `DisposeAsync()` | `ValueTask` | 释放 JS 句柄。 |

### 备注

- 松开没有落在愿意接收的插槽上（包括松回发送口）时，`OnSlotConnectionEnd` 会重置虚拟连线。
- `SlotView` 已经打开本组件；再包一层会让测量与手势都翻倍。

## 类：WorkflowSlotLayoutBehavior

`public partial class WorkflowSlotLayoutBehavior : ComponentBase, IAsyncDisposable`

测量被包住的槽元素（它们带 `data-slot-id`）在屏幕上的中心，并以画布坐标把锚点写回。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `Node` | `INodeComponent?` | `null` | 要同步插槽的节点。 |
| `IsEnabled` | `bool` | `false` | 加载 JS 槽布局初始化器。 |
| `CoordinateHostId` | `string?` | `null` | 预留的坐标宿主 id。 |
| `ChildContent` | `RenderFragment?` | `null` | 含槽元素的节点内容。 |

### 方法

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `OnSlotLayoutBatch(string[][] batch)` | `void` | `[JSInvokable]`；每项为 `[slotId, canvasLocalX, canvasLocalY]`。 |
| `DisposeAsync()` | `ValueTask` | 停止流水线并释放 JS 句柄。 |

### 备注

- JS 的 rAF/ResizeObserver 调度决定测量时机；组件只把一批读数喂给共享的 `SlotLayoutPipelineCore`。
- 读数用 `InvariantCulture` 解析；逗号小数的服务器否则会静默放错锚点。
- 写过锚点时，组件会通知节点其 `Anchor` 已变化，连线因此在拖动中立刻重画。

## 枚举：SurfacePointerKind

`public enum SurfacePointerKind`

| 成员 | 值 | 含义 |
| --- | --- | --- |
| `Entered` | `0` | 指针到达元素上方。 |
| `Moved` | `1` | 指针移动。 |
| `Exited` | `2` | 指针离开元素。 |
| `Pressed` | `3` | 按键按下。 |
| `Released` | `4` | 按键抬起。 |
| `Wheel` | `5` | 滚轮转动。 |

`RoutePointerAsync` 把它们映射到对应的 Core `PointerEventArgs` 子类。这是浏览器边界的枚举，不是 Core 的输入阶段。
