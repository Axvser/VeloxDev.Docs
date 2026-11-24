# 小地图

`MinimapPipelineCore` 是平台中立的小地图状态机。节点、连线与视口变化只设置脏标记并触发 `RenderRequested`；映射与布局工作在下一次渲染或刷新时做一次。

## 正常流程：映射与绘制

```plantuml
@startuml
!theme plain

actor "适配器" as Adapter
participant "MinimapPipelineCore" as Pipe
participant "Tree" as Tree
participant "WorkflowSurfaceMath" as Math
participant "IMinimapRenderer" as Renderer

Adapter -> Pipe: Tree = tree
activate Pipe
Pipe -> Pipe: UnsubscribeFromTree / SubscribeToTree
Pipe -> Pipe: Invalidate（dirty = true，RenderRequested）
deactivate Pipe

Adapter -> Pipe: Render(surface)
activate Pipe
alt 不可见或已释放
    Pipe --> Adapter: 返回
end
Pipe -> Pipe: Refresh()
alt dirty
    Pipe -> Tree: 枚举 Nodes
    Pipe -> Tree: node.Anchor / node.Size
    Pipe -> Math: WorkflowBounds.FromNodes
    Pipe -> Math: ToCanvasLocal(scroll, contentOffset)
    Pipe -> Math: MinimapFit(content, minimap size, padding)
    Pipe -> Math: MinimapLocal 逐节点
    Pipe -> Math: MinimapViewportRect
    Pipe -> Pipe: drawContext = new MinimapDrawContext
end
Pipe -> Renderer: Render(surface, drawContext)
deactivate Pipe
@enduml
```

```csharp
public void Render(TSurface surface)
{
    if (disposed || !IsVisible)
    {
        return;
    }

    Refresh();
    if (drawContext is null)
    {
        return;
    }

    Renderer.Render(surface, drawContext);
}
```

> 来源：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs` 第 188-202 行。

`BuildDrawContext` 把节点矩形与视口矩形转换成画布局部边界，把内容适配进小地图，并按最小缩略尺寸映射每个节点。

```csharp
var (ox, oy, sc) = WorkflowSurfaceMath.MinimapFit(
    ContentBounds.Width, ContentBounds.Height, mmW - pad * 2, mmH - pad * 2, pad);

// ...
var (l, t) = WorkflowSurfaceMath.MinimapLocal(
    nx, ny, ContentBounds.Left, ContentBounds.Top, ox, oy, sc);
mapped.Add(WorkflowBounds.FromNode(
    l, t,
    WorkflowSurfaceMath.MinThumbSize(nw, sc, minThumb),
    WorkflowSurfaceMath.MinThumbSize(nh, sc, minThumb)));
```

> 来源：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs` 第 328-342 行。

## 拖拽滚动

在小地图内按下会刷新映射、把视口中心移到按下点、捕获指针并开始拖拽。每次移动重新居中；松手结束。

```plantuml
@startuml
!theme plain

actor "适配器" as Adapter
participant "MinimapPipelineCore" as Pipe
participant "IMinimapInputHost" as Input
participant "IMinimapViewportHost" as Viewport
participant "WorkflowSurfaceMath" as Math

Adapter -> Pipe: PointerPressed()
activate Pipe
Pipe -> Input: IsPressed / PointerPosition
alt 不在小地图内
    Pipe --> Adapter: false
else 在内
    Pipe -> Pipe: Refresh()
    Pipe -> Pipe: NavigateTo(x, y)
    Pipe -> Math: MinimapToCanvasLocal
    Pipe -> Math: MinimapToScroll
    Pipe -> Math: ClampScrollOffset
    Pipe -> Viewport: ApplyScroll(x, y)
    Pipe -> Input: Capture()
    Pipe --> Adapter: true
end
deactivate Pipe

Adapter -> Pipe: PointerMoved()
activate Pipe
Pipe -> Pipe: NavigateTo(pointer)
deactivate Pipe

Adapter -> Pipe: PointerReleased()
activate Pipe
Pipe -> Input: Release()
deactivate Pipe
@enduml
```

```csharp
public bool PointerPressed()
{
    if (disposed || dragging || !Input.IsPressed)
    {
        return false;
    }

    var (x, y) = Input.PointerPosition;
    if (!HitTest(x, y))
    {
        return false;
    }

    Refresh();
    NavigateTo(x, y);
    dragging = true;
    Input.Capture();
    return true;
}
```

> 来源：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs` 第 215-233 行。

## 失效

管线订阅节点与连线集合变化，以及 `Anchor`/`Size` 属性变化。每次变化调用 `Invalidate`，设置 `dirty` 并触发 `RenderRequested`；一串变化因此只花一次映射。

```csharp
public void Invalidate()
{
    if (disposed)
    {
        return;
    }

    dirty = true;
    RenderRequested?.Invoke(this, EventArgs.Empty);
}
```

> 来源：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs` 第 163-172 行。

> 来源：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs` 第 413-631 行。

## 错误与边界路径

- **没有树**：`BuildDrawContext` 返回 null 并清空缓存边界。
- **没有节点**：内容边界为空时不产生绘制上下文，不绘制。
- **比例非法**：`Scale <= 0` 时 `NavigateTo` 返回。
- **不可见**：`Render` 在刷新前返回，但命中测试与拖拽算术仍然可用。
- **指针在外**：`PointerPressed` 返回 false 且不捕获。
- **捕获丢失**：`PointerCaptureLost` 结束拖拽且不再请求捕获。
- **线程亲和**：树通知可能来自任意线程；适配器必须把 `Invalidate` 与渲染调用编组到宿主线程。

> 来源：`Src/Core/VeloxDev.Core/WorkflowSystem/Minimap/MinimapPipelineCore.cs` 第 50-59、141-145、188-202、259-269、294-322、378-392 行。
