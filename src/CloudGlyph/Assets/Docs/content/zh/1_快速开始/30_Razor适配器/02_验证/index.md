# 验证与完整代码

## 运行

```powershell
dotnet run
```

打开启动器打印的 HTTPS 地址并访问 `/`。

**预期结果**，按顺序：

1. 表面铺满页面，世界网格与上/左标尺带可见。
2. 两个节点卡片以及它们之间的连线可见。
3. 拖动卡片标题条会移动卡片；画布不平移。
4. 拖动空白表面会平移，指针下面的世界点保持不动。
5. Ctrl+滚轮绕指针缩放；卡片文字、端口与连线一起缩放。
6. 从端口拖出橡皮筋；在另一张卡片的合法端口上释放会再创建一条连线。
7. 右键点击连线会打开你在 `<LinkMenu>` 里声明的菜单。

## 连线菜单默认是空的

生成的 `TreeView.razor` 声明菜单片段，但不加任何条目：

```razor
<LinkMenu Context="link">
</LinkMenu>
```

每个条目都会收到被右键的那条连线，所以一行就是一个完整动作：

```razor
<LinkMenu Context="link">
    <button type="button" @onclick="() => link.DeleteCommand.Execute(null)">Delete</button>
</LinkMenu>
```

这家没有菜单项的绑定语法，所以处理器保持内联。表面负责渲染菜单外壳、定位它，并在菜单打开时暂停输入路由。

## 为什么缩放需要 JS 那一半

`ZoomEnabled` 打开组件侧行为；真正的缩放由 `_content/VeloxDev.Razor/veloxdev.workflow.js` 里的非被动 `wheel` 监听器执行。缩放后 JS 在下一个动画帧派发 `veloxdev-wf-layout-changed`，插槽布局监听它并重新测量。自己写缩放路径时也要派发同一事件，否则卡片在动而端口停在旧位置。

滚轮监听器还把普通滚轮的增量交给服务端；表面通过 `WorkflowInput.Scroller` 路由，除非有订阅者拒绝了这次事件。

## 完整代码

`Components/Pages/Home.razor`。四个 ViewModel 定义在[表面与宿主](../01_表面与宿主/index.md)；生成的组件就是那一页里的十四个文件。

```razor
@page "/"
@rendermode RenderMode.InteractiveServer
@using VeloxDev.WorkflowSystem

<PageTitle>VeloxDev Workflow</PageTitle>

<div style="position:relative;width:100vw;height:100vh;">
    @if (_tree is not null)
    {
        <TreeView Tree="_tree" />
    }
</div>

@code {
    private TreeViewModel? _tree;

    protected override void OnInitialized()
    {
        _tree = new TreeViewModel();
        LoadSample(_tree);
    }

    private static void LoadSample(TreeViewModel tree)
    {
        tree.Layout.NegativeOffset = new Offset(320, 260);
        var size = new Size(260, 180);

        var source = new NodeViewModel
        {
            Name = "Source",
            Size = size,
            Anchor = new Anchor { Horizontal = 0, Vertical = 0 }
        };
        var sink = new NodeViewModel
        {
            Name = "Sink",
            Size = size,
            Anchor = new Anchor { Horizontal = 360, Vertical = 0 }
        };

        tree.CreateNodeCommand.Execute(source);
        tree.CreateNodeCommand.Execute(sink);

        source.OutputSlots.SetSelector(typeof(bool));
        source.InputSlot.SetChannelCommand.Execute(SlotChannel.OneSource);
        sink.InputSlot.SetChannelCommand.Execute(SlotChannel.MultipleSources);

        if (source.OutputSlots.Items.FirstOrDefault()?.Slot is { } sender)
        {
            tree.Links.Add(new LinkDefaultViewModel
            {
                Sender = sender,
                Receiver = sink.InputSlot,
                IsVisible = true
            });
        }
    }
}
```

符号来源：

- `TreeViewModel`、`NodeViewModel`、`SlotViewModel`、`VirtualizeHelper` —— [表面与宿主](../01_表面与宿主/index.md)。
- `TreeView`、`NodeView`、`SlotView`、`LinkView`、`TemplateSelector`、`GridDecorator`、`MinimapOverlay` —— 由 `razor-v-*` 生成；镜像在 `Examples/Workflow/Blazor Trimmed/Demo/Components/Workflow/`。
- `WorkflowSurfaceBehavior`、`WorkflowPresentation` —— `Src/Adapters/VeloxDev.Razor/WorkflowSystem/AttachedBehaviors/`。

## 运行声明

⚠️ 未实际运行 —— 2026-11-25 仅对照当前源码与 `Examples/Workflow/Blazor Trimmed/Demo/` 静态核验。本页复刻了 demo 的调用序列，但这里没有记录构建或浏览器输出。
