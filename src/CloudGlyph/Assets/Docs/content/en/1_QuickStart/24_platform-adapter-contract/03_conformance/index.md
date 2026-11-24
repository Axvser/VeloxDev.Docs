# Conformance

The contract is checked by driving **one graph** through **one set of assertions** on every adapter that has a windowless host. The shared fixture is `VeloxDev.AdapterTestKit.TestGraph`; the suites live under `Src/Test/Headless/`.

## What the kit drives

`TestGraph.Create(bool connect = true)` builds a deterministic tree: a left node and a right node, an output slot and an input slot, an optional link between them, and a far-away node that only a scrolled viewport can see. It uses the helpers directly, not the generated commands, so a failure reports the adapter rather than the command pipeline.

```csharp
var graph = TestGraph.Create();       // left → right link
var tree = graph.Tree;                // TreeDefaultViewModel with TreeHelper(200)
var far = graph.Far;                  // outside the default viewport
```

The suites assert the same surface contract:

1. `IsEnabled == false` makes `Refresh` a no-op in the suites whose surface honours the switch; WinForms' `Refresh` does not read it.
2. Attached parts are resolved; the canvas transform and the grid decorator receive the same content offset.
3. Scrolling writes `tree.GetHelper().Viewport` and `Layout.ViewportOffset` from the same source.
4. `Layout.ViewportOffset` is restored to the scroll container after attach.
5. `VisibleItems` enters and leaves nodes with the viewport.
6. `ViewPool` creates one view per visible item.
7. Detaching stops the surface writing to the model.
8. Avalonia additionally drives real pointer input for the Ctrl+wheel direction and the `[0.1, 10]` clamp.

WinUI and MAUI have demos but **no headless suite** — `Src/Test/Headless/README.md` records that they have no windowless host.

## Complete code

A single MSTest class that builds the WPF surface in code and asserts the shared pieces. It is deliberately the same shape as `WpfHeadlessSurface` in the WPF suite, reduced to one test.

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
        Assert.IsNotNull(input.Scroller, "the surface registers a scroller");
        Assert.IsNotNull(input.Navigator, "the surface registers a navigator");
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

The test project file needs the three references from [Prerequisites](../00_prerequisites/index.md) and `net8.0-windows` with `UseWPF`.

**Expected result:** `TestGraph.Create()` is not null, `surface` constructs without throwing, and the test method reports `Passed`.

## Run it

```powershell
dotnet test Src/Test/Headless/VeloxDev.WPF.Headless.Tests/VeloxDev.WPF.Headless.Tests.csproj
```

The repository's full headless run and coverage floor are:

```powershell
./Src/Test/Headless/run-headless-tests.ps1
./Src/Test/Headless/check-coverage.ps1
```

**Expected result:** all suites pass; `check-coverage.ps1` compares each adapter's line coverage with the floor recorded in `Src/Test/Headless/README.md` and fails only when a floor regresses.

## Run Declaration

- ⚠️ Not actually run — statically verified only. The API names, target frameworks, test names and command lines were checked against `Src/Core/VeloxDev.Core/`, `Src/Adapters/`, `Src/Test/Headless/` and `Src/Test/Headless/README.md`; the complete-code block was not compiled or executed in the writing session.
