# 输入路由

`WorkflowInput` 是每棵树一条的路由。适配器把原生事件翻译成 `PointerEventArgs` 或 `KeyEventArgs` 并调用 `Route`；沿途每个 Helper 暴露一个 `InputRelay`；每一跳收到的是同一个 `WorkflowEventHandle`。

## WorkflowInput

```csharp
public sealed class WorkflowInput
```

一棵树一个实例。树活着期间，`For` 返回的永远是同一个对象。

### 属性

| 成员 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `Tree` | `ITreeComponent` | get | 这条路由所属的树。 |
| `PointerTarget` | `IWorkflowComponent?` | get | 指针当前所在的组件；空白画布上或挂起时为 `null`。 |
| `HoveredLink` | `ILinkComponent?` | get | `PointerTarget as ILinkComponent`。 |
| `ConnectionSender` | `ISlotComponent?` | get | 连线拖动起始的端口。 |
| `PreviewReceiver` | `ISlotComponent?` | get | 连线拖动期间的候选接收端口。 |
| `PreviewState` | `ConnectionPreviewState` | get | 当前预览状态。 |
| `PreviewCheck` | `ConnectionCheck?` | get | 当前连接检查结果。 |
| `HitRadius` | `double` | get/set | 指针命中半径；默认 `LinkHitTestEx.DefaultHitRadius`（6）。 |
| `IsSuspended` | `bool` | get/set | 为 `true` 时指针移动不更新 `PointerTarget`；默认 `false`。 |
| `Scroller` | `IWorkflowSurfaceScroller?` | get/set | 挂载表面注册的 scroller；没有时为 `null`。 |
| `Navigator` | `IWorkflowSurfaceNavigator?` | get/set | 挂载表面注册的 navigator；没有时为 `null`。 |

### 事件

| 事件 | 参数 | 说明 |
|---|---|---|
| `PreviewChanged` | `EventHandler<ConnectionPreviewEventArgs>` | 连接预览变化时触发。 |
| `PreviewValidating` | `EventHandler<ConnectionPreviewValidatingEventArgs>` | 框架接受的每个候选连接在宿主校验前触发一次。 |

### 方法

| 签名 | 返回 | 说明 |
|---|---|---|
| `WorkflowInput(ITreeComponent tree)` | — | 为一棵树创建路由。`tree` 为 null 时抛 `ArgumentNullException`。 |
| `static WorkflowInput For(ITreeComponent tree)` | `WorkflowInput` | 返回每棵树共享的路由，首次使用时创建。`tree` 为 null 时抛 `ArgumentNullException`。 |
| `Route(PointerEventArgs e)` | `void` | 目标变化时先触发 `PointerExited`/`PointerEntered`，再依次走过目标、祖先、树。`e` 为 null 时抛 `ArgumentNullException`。 |
| `Route(KeyEventArgs e)` | `void` | 按键事件走同一条链。`e` 为 null 时抛 `ArgumentNullException`。 |

连接预览的属性与事件属于连接功能；它们放在这里，是因为路由持有它们。

## IInputEvents 与 InputRelay

```csharp
public interface IInputEvents
{
    InputRelay Input { get; }
}

public sealed class InputRelay
```

`IInputEvents` 是承载路由输入的可选 Helper 能力。默认的树、节点、插槽与连线 Helper 都实现了它。

| 事件 | 参数 |
|---|---|
| `PointerEntered` | `EventHandler<PointerEnteredEventArgs>` |
| `PointerExited` | `EventHandler<PointerExitedEventArgs>` |
| `PointerMoved` | `EventHandler<PointerMovedEventArgs>` |
| `PointerPressed` | `EventHandler<PointerPressedEventArgs>` |
| `PointerReleased` | `EventHandler<PointerReleasedEventArgs>` |
| `PointerWheelChanged` | `EventHandler<PointerWheelEventArgs>` |
| `KeyDown` | `EventHandler<KeyDownEventArgs>` |
| `KeyUp` | `EventHandler<KeyUpEventArgs>` |

`Raise(PointerEventArgs)` 与 `Raise(KeyEventArgs)` 是 internal；适配器通过 `WorkflowInput` 路由，而不是直接调 relay。

## WorkflowEventHandle

```csharp
public sealed class WorkflowEventHandle
```

一个逻辑动作配一个句柄。靠近目标的订阅者与树上的订阅者拿到的是同一个实例。

| 成员 | 类型 | 访问 | 默认 | 说明 |
|---|---|---|---|---|
| `PreventDefault` | `bool` | get/set | `false` | 抑制框架自己对这次动作的反应。 |
| `StopPropagation` | `bool` | get/set | `false` | 在此停止冒泡；祖先 Helper 不再收到。 |

## 指针事件参数

```csharp
public abstract class PointerEventArgs : EventArgs
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Position` | `Anchor` | 表面坐标；`Anchor.Layer` 是来源视图的层。 |
| `Modifiers` | `InputModifiers` | 事件期间按住的修饰键。 |
| `Source` | `object?` | 输入来自的视图。 |
| `Target` | `IWorkflowComponent?` | 命中的组件；空白画布上为 `null`。每一跳看到的都是原始目标。 |
| `Handle` | `WorkflowEventHandle` | 本次动作的句柄。 |

受保护构造函数接收 `(Anchor position, InputModifiers modifiers, object? source, IWorkflowComponent? target, WorkflowEventHandle handle)`，位置或句柄为 null 时抛 `ArgumentNullException`。

| 类型 | 额外成员 |
|---|---|
| `PointerEnteredEventArgs` | — |
| `PointerExitedEventArgs` | — |
| `PointerMovedEventArgs` | — |
| `PointerPressedEventArgs` | `MouseButton Button`、`int ClickCount` |
| `PointerReleasedEventArgs` | `MouseButton Button`、`int ClickCount` |
| `PointerWheelEventArgs` | `double DeltaX`、`double DeltaY` |

`DeltaY` 以远离用户为正（滚轮向上），各平台已统一符号。非倾斜滚轮上 `DeltaX` 为 0；只有符号是契约。

## 按键事件参数

```csharp
public abstract class KeyEventArgs : EventArgs
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Key` | `InputKey` | 映射后的按键。 |
| `RawKeyCode` | `int` | 平台原生键码；不可跨适配器比较。 |
| `Modifiers` | `InputModifiers` | 事件期间按住的修饰键。 |
| `IsRepeat` | `bool` | 尽力而为；`false` 表示「未报告为重复」。 |
| `Source` | `object?` | 获得焦点的视图。 |
| `Target` | `IWorkflowComponent?` | 适配器把按键应用到哪个组件。 |
| `Handle` | `WorkflowEventHandle` | 本次动作的句柄。 |

`KeyDownEventArgs` 与 `KeyUpEventArgs` 没有额外成员。Core 没有默认按键动作；`Delete` 或 `Ctrl+Z` 做什么由宿主决定。

## 枚举

```csharp
public enum MouseButton
{
    None = 0, Left = 1, Right = 2, Middle = 3, XButton1 = 4, XButton2 = 5
}

[Flags]
public enum InputModifiers
{
    None = 0, Alt = 1, Control = 2, Shift = 4, Meta = 8
}
```

`InputKey` 是一套精选的、平台中立的键集。它没有命名的键映射到 `Unknown`，仍可通过 `RawKeyCode` 还原。

| 区间 | 成员 |
|---|---|
| 控制键 | `Unknown=0`、`None=1`、`Cancel=2`、`Back=3`、`Tab=4`、`Enter=5`、`Escape=6`、`Space=7`、`PageUp=8`、`PageDown=9`、`End=10`、`Home=11`、`Left=12`、`Up=13`、`Right=14`、`Down=15`、`Insert=16`、`Delete=17` |
| 修饰键 | `LeftShift=18`、`RightShift=19`、`LeftCtrl=20`、`RightCtrl=21`、`LeftAlt=22`、`RightAlt=23`、`LWin=24`、`RWin=25` |
| 字母 | `A=30`、`B=31`、`C=32`、`D=33`、`E=34`、`F=35`、`G=36`、`H=37`、`I=38`、`J=39`、`K=40`、`L=41`、`M=42`、`N=43`、`O=44`、`P=45`、`Q=46`、`R=47`、`S=48`、`T=49`、`U=50`、`V=51`、`W=52`、`X=53`、`Y=54`、`Z=55` |
| 数字 | `D0=60`、`D1=61`、`D2=62`、`D3=63`、`D4=64`、`D5=65`、`D6=66`、`D7=67`、`D8=68`、`D9=69` |
| 功能键 | `F1=80`、`F2=81`、`F3=82`、`F4=83`、`F5=84`、`F6=85`、`F7=86`、`F8=87`、`F9=88`、`F10=89`、`F11=90`、`F12=91` |
