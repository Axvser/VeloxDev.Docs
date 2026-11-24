# 路由输入

Core 只路由输入，从不对它动手。一次按键、一次滚轮或一次指针移动，会先送到指针底下那个组件的 Helper，再送到它的祖先，最后送到树。订阅就是在某个组件的 `InputRelay` 上订阅；否决就是写那个随事件旅行的 `WorkflowEventHandle`。

## 一棵树一条路由

`WorkflowInput.For(tree)` 对同一棵树在树的生命周期内返回同一个实例。适配器往里转发，宿主从它读取当前指针目标与滚动能力。

```csharp
var input = WorkflowInput.For(tree);

// The route maintains this read-only state.
IWorkflowComponent? under = input.PointerTarget;   // null over empty canvas
ILinkComponent? hovered = input.HoveredLink;

// Optional capabilities registered by an attached adapter.
IWorkflowSurfaceScroller? scroller = input.Scroller;
IWorkflowSurfaceNavigator? navigator = input.Navigator;
```

路由只拥有一项状态——指针停在哪个组件上。宿主可能期待的其它东西（选中、悬停绘制、删除）都归宿主。

## 在 Helper 上订阅

每个默认 Helper 都实现 `IInputEvents`。树 Helper、节点 Helper、插槽 Helper、连线 Helper 暴露同一个 `InputRelay`。

```csharp
if (tree.GetHelper() is not IInputEvents events) return;

events.Input.KeyDown += OnKeyDown;
events.Input.PointerWheelChanged += OnWheel;
```

事件参数是 `PointerEventArgs` 与 `KeyEventArgs` 的具体子类：

| 事件 | 参数 | 额外成员 |
|---|---|---|
| `PointerEntered` / `PointerExited` / `PointerMoved` | `PointerEnteredEventArgs` / `PointerExitedEventArgs` / `PointerMovedEventArgs` | — |
| `PointerPressed` / `PointerReleased` | `PointerPressedEventArgs` / `PointerReleasedEventArgs` | `Button`、`ClickCount` |
| `PointerWheelChanged` | `PointerWheelEventArgs` | `DeltaX`、`DeltaY` |
| `KeyDown` / `KeyUp` | `KeyDownEventArgs` / `KeyUpEventArgs` | `Key`、`RawKeyCode`、`IsRepeat` |

每个参数都带 `Position`、`Modifiers`、`Source`（视图）、`Target`（组件，空白画布为 `null`）与 `Handle`。`Target` 在每一跳都是最初那个目标——祖先不会看到自己。

## 否决，而不是重写

`WorkflowEventHandle` 有两个互相独立的标志：

- `PreventDefault` —— 框架自己那一手不执行。在路由的指针或按键事件上，那一手归适配器（滚轮滚动、平移、节点拖动、连线拖动）。在模型 `…ing` 事件上，它表示直接拒绝这个动作。
- `StopPropagation` —— 事件停在这里，祖先 Helper 一个都收不到。

一个句柄随一个动作旅行，所以靠近目标的订阅者与树上的订阅者读到同一个实例。两个标志都不设是默认行为，什么也不改变。

```csharp
private void OnKeyDown(object? sender, KeyDownEventArgs e)
{
    if (!e.Modifiers.HasFlag(InputModifiers.Control)) return;
    if (_tree is not { } tree) return;

    var redo = e.Modifiers.HasFlag(InputModifiers.Shift);
    if (e.Key == InputKey.Z && !redo) tree.UndoCommand.Execute(null);
    else if (e.Key == InputKey.Y || (e.Key == InputKey.Z && redo)) tree.RedoCommand.Execute(null);
    else return;

    e.Handle.PreventDefault = true;
}
```

节点拖动与插槽连线不是模型动作，按设计不可撤销。拖完之后按 `Ctrl+Z` 撤的是最近一次结构改动，不是那次拖动；要让拖动可撤销，就自己提供一个 `IActionPair` 走 `tree.GetHelper().Submit(...)`。

## 滚轮归适配器，直到你接管

适配器阻止平台滚动容器去滚工作流表面，并自己执行滚动。所以普通滚轮仍然执行默认的纵向滚动。如果订阅者设置了 `PreventDefault`，这一笔就不滚，由订阅者通过 `WorkflowInput.Scroller` 决定滚到哪里。

```csharp
// Horizontal scrolling on Shift+wheel, exactly as the WPF Trimmed demo writes it.
private void OnWheel(object? sender, PointerWheelEventArgs e)
{
    if (!e.Modifiers.HasFlag(InputModifiers.Shift) || _tree is not { } tree) return;

    e.Handle.PreventDefault = true;

    // Vertical positive is "away from the user"; the horizontal axis positive is "right".
    // The two axes are not the same physical direction, so the sign is flipped here.
    WorkflowInput.For(tree).Scroller?.ScrollBy(-e.DeltaY, 0d);
}
```

读 `e.Modifiers`，不要读键盘状态。修饰键随滚轮事件一起来，不依赖哪个元素持有键盘焦点；改用 `KeyDown`/`KeyUp` 跟踪 `Shift` 的话，表面没有焦点时 Shift+滚轮会失效。

## Delete 与其它按键

Core 没有默认按键动作。适配器负责路由，宿主负责决定：

```csharp
events.Input.KeyDown += (_, e) =>
{
    if (e.Key != InputKey.Delete || e.Handle.PreventDefault) return;
    if (e.Target is not ILinkComponent link || !link.DeleteCommand.CanExecute(null)) return;
    link.DeleteCommand.Execute(null);
};
```

按键的 `Target` 就是指针所在的组件：键本身没有位置。树级的键（例如 `Ctrl+Z`）在指针位于空白画布时也能到树，因为链的尽头永远是树。

## 指针进入与离开

指针移到另一个组件上时，路由先给离开的那个发 `PointerExited`，再给到达的那个发 `PointerEntered`，各自带一个新句柄。组件视图只订自己的 Helper 就能听完整的悬停过程——不必在每次移动时比较 target。

## 预期结果

- 指针在表面任何位置时，`Ctrl+Z` / `Ctrl+Y` 都能撤销、重做结构改动。
- `Shift` + 滚轮横向滚动；普通滚轮纵向滚动。
- 指针在连线上按 `Delete` 删除它；在节点上按则什么也不做，除非你写了处理。
- 在按下处理里设置 `e.Handle.PreventDefault`，适配器这一次就不会平移或拖动。

## 下一页

[导航](../03_导航/index.md)介绍内置手势与两项导航能力。
