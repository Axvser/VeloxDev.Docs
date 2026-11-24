# 一致性验证

契约的验证方式是：把**一棵图**交给**同一组断言**，在每一个有无头宿主的适配器上各跑一遍。共享夹具是 `VeloxDev.AdapterTestKit.TestGraph`；套件在 `Src/Test/Headless/` 下。

## 套件驱动什么

`TestGraph.Create(bool connect = true)` 建一棵确定的树：左节点、右节点、一个输出口与一个输入口、两者之间可选的连线，以及一个只有滚动视口才看得见的远处节点。它直接用 helper，不走生成的命令，这样失败报告的是适配器而不是命令管线。

```csharp
var graph = TestGraph.Create();       // 左 → 右 的连线
var tree = graph.Tree;                // TreeDefaultViewModel，Helper 是 TreeHelper(200)
var far = graph.Far;                  // 在默认视口之外
```

各套件断言同一组表面契约：

1. `IsEnabled == false` 时，尊重这个开关的表面会让 `Refresh` 成为 no-op；WinForms 的 `Refresh` 不读它。
2. 命名部件被解析；画布变换与网格装饰器拿到相同的内容偏移。
3. 滚动同时写入 `tree.GetHelper().Viewport` 与 `Layout.ViewportOffset`，两者同源。
4. 挂载后 `Layout.ViewportOffset` 被恢复到滚动容器。
5. `VisibleItems` 随视口进/出节点。
6. `ViewPool` 为每个可见项创建一个视图。
7. 卸载后表面不再写模型。
8. Avalonia 额外用真实指针输入验证 Ctrl+滚轮方向与 `[0.1, 10]` 夹取。

WinUI 与 MAUI 有 demo，但**没有无头套件** —— `Src/Test/Headless/README.md` 记录它们没有窗口无关的宿主。

## 完整代码

一个 MSTest 类：用代码搭出 WPF 表面，并断言共享部件。它的形状刻意与 WPF 套件里的 `WpfHeadlessSurface` 相同，只是压到一个测试。

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using System.Windows.Threading;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using VeloxDev.AdapterTestKit;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.AttachedBehaviors;
using WfSize = VeloxDev.WorkflowSystem.Size;

namespace ContractQuickStart;

[STATestClass]
public sealed class SurfaceContractSmokeTests
{
    [TestMethod]
    public void Attach_PublishesTheSharedSurface()
    {
        var graph = TestGraph.Create();
        using var surface = new CodeSurface(graph);
        var helper = graph.Tree.GetHelper();

        var input = WorkflowInput.For(graph.Tree);
        Assert.IsNotNull(input.Scroller, "surface registers a scroller");
        Assert.IsNotNull(input.Navigator, "surface registers a navigator");
        Assert.IsTrue(helper.Viewport.Width > 0, "the viewport is measured");

        CollectionAssert.Contains(helper.VisibleItems, graph.Left);
        CollectionAssert.Contains(helper.VisibleItems, graph.Right);
        CollectionAssert.DoesNotContain(helper.VisibleItems, graph.Far);

        surface.ScrollTo(120, 80);
        Assert.AreEqual(120d, helper.Viewport.Horizontal, 0.5);
        var released = helper.Viewport.Horizontal;

        surface.Detach();
        surface.ScrollTo(0, 0);
        Assert.AreEqual(released, helper.Viewport.Horizontal, 0.5,
            "a detached surface no longer writes the viewport");
    }
}

internal sealed class CodeSurface : IDisposable
{
    private const double HostWidth = 800d;
    private const double HostHeight = 600d;

    public CodeSurface(TestGraph graph)
    {
        Tree = graph.Tree;
        Tree.Layout.OriginSize = new WfSize(8000, 6000);

        var border = new Border { Background = Brushes.Transparent, Child = Scroll };
        Scroll.Content = Canvas;
        Decorator.Children.Add(border);
        Host = new UserControl { Width = HostWidth, Height = HostHeight, DataContext = Tree, Content = Decorator };

        Canvas.Width = 8000;
        Canvas.Height = 6000;
        Canvas.Background = Brushes.Transparent;
        Canvas.SetBinding(FrameworkElement.WidthProperty,
            new Binding("ActualSize.Width") { Source = Tree.Layout });
        Canvas.SetBinding(FrameworkElement.HeightProperty,
            new Binding("ActualSize.Height") { Source = Tree.Layout });

        var scope = new NameScope();
        NameScope.SetNameScope(Host, scope);
        scope.RegisterName("PART_ScrollViewer", Scroll);
        scope.RegisterName("PART_Canvas", Canvas);
        scope.RegisterName("PART_GridDecorator", Decorator);
        scope.RegisterName("PART_SurfaceBorder", border);

        WorkflowSurfaceBehavior.SetScrollViewerName(Host, "PART_ScrollViewer");
        WorkflowSurfaceBehavior.SetCanvasName(Host, "PART_Canvas");
        WorkflowSurfaceBehavior.SetGridDecoratorName(Host, "PART_GridDecorator");
        WorkflowSurfaceBehavior.SetPointerPressSourceName(Host, "PART_SurfaceBorder");
        WorkflowSurfaceBehavior.SetZoomEnabled(Host, true);

        ViewPool.SetItemsSource(Canvas, Tree.GetHelper().VisibleItems);
        ViewPool.SetTemplateSelector(Canvas, new AnyTemplateSelector());

        Layout();
        WorkflowSurfaceBehavior.SetIsEnabled(Host, true);
        WorkflowSurfaceBehavior.Refresh(Host);
        Pump();
    }

    public TreeDefaultViewModel Tree { get; }
    public UserControl Host { get; }
    public ScrollViewer Scroll { get; } = new();
    public Canvas Canvas { get; } = new();
    public TestDecorator Decorator { get; } = new();

    public void Layout()
    {
        Host.Measure(new System.Windows.Size(HostWidth, HostHeight));
        Host.Arrange(new Rect(0, 0, HostWidth, HostHeight));
        Host.UpdateLayout();
    }

    public void ScrollTo(double x, double y)
    {
        Scroll.ScrollToHorizontalOffset(x);
        Scroll.ScrollToVerticalOffset(y);
        Scroll.UpdateLayout();
        Pump();
    }

    public void Detach() => WorkflowSurfaceBehavior.SetIsEnabled(Host, false);

    public void Dispose()
    {
        Detach();
        Host.Content = null;
        Pump();
    }

    public static void Pump()
    {
        var frame = new DispatcherFrame();
        Dispatcher.CurrentDispatcher.BeginInvoke(
            DispatcherPriority.ApplicationIdle, new Action(() => frame.Continue = false));
        Dispatcher.PushFrame(frame);
    }
}

internal sealed class TestDecorator : Grid, IWorkflowGridDecorator
{
    public double ScrollOffsetX { get; set; }
    public double ScrollOffsetY { get; set; }
    public double ContentOffsetX { get; set; }
    public double ContentOffsetY { get; set; }
    public double RulerBand => 0d;
}

internal sealed class AnyTemplateSelector : DataTemplateSelector
{
    private static readonly DataTemplate View = new() { VisualTree = new FrameworkElementFactory(typeof(Border)) };

    public override DataTemplate SelectTemplate(object item, DependencyObject container) => View;
}
```

测试工程需要[前置条件](../00_前置条件/index.md)里的三条引用，以及 `net8.0-windows` + `UseWPF`。

**预期结果：** `TestGraph.Create()` 非空，`surface` 构造不抛异常，测试方法报告 `Passed`。

## 运行

```powershell
dotnet test Src/Test/Headless/VeloxDev.WPF.Headless.Tests/VeloxDev.WPF.Headless.Tests.csproj
```

仓库完整无头运行与覆盖率地板：

```powershell
./Src/Test/Headless/run-headless-tests.ps1
./Src/Test/Headless/check-coverage.ps1
```

**预期结果：** 所有套件通过；`check-coverage.ps1` 把每家的行覆盖与 `Src/Test/Headless/README.md` 记录的地板对比，只有地板回退时才失败。

## 运行声明

- ⚠️ 未实际运行 —— 仅做了静态核对。API 名、目标框架、测试名与命令行均对照过 `Src/Core/VeloxDev.Core/`、`Src/Adapters/`、`Src/Test/Headless/` 与 `Src/Test/Headless/README.md`；完整代码块在本次写作中未编译、未执行。
