# 输入枚举

三个小枚举让输入在各适配器之间保持一致：按键身份、修饰键标志与鼠标按键。适配器把原生值映射到这些枚举；宿主永远看不到平台枚举。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## InputKey

**签名：** `enum InputKey`

| 分组 | 成员 |
| --- | --- |
| 未映射 / 控制 | `Unknown = 0`、`None = 1`、`Cancel = 2`、`Back = 3`、`Tab = 4`、`Enter = 5`、`Escape = 6`、`Space = 7` |
| 导航 | `PageUp = 8`、`PageDown = 9`、`End = 10`、`Home = 11`、`Left = 12`、`Up = 13`、`Right = 14`、`Down = 15`、`Insert = 16`、`Delete = 17` |
| 修饰键 | `LeftShift = 18`、`RightShift = 19`、`LeftCtrl = 20`、`RightCtrl = 21`、`LeftAlt = 22`、`RightAlt = 23`、`LWin = 24`、`RWin = 25` |
| 字母 | `A = 30` 到 `Z = 55`（连续） |
| 数字 | `D0 = 60` 到 `D9 = 69`（连续） |
| 功能键 | `F1 = 80` 到 `F12 = 91`（连续） |

无法命名某个键的适配器报告 `Unknown`，并通过 `KeyEventArgs.RawKeyCode` 提供真实键码。

## InputModifiers

**签名：** `[Flags] enum InputModifiers`

| 成员 | 值 |
| --- | --- |
| `None` | `0` |
| `Alt` | `1` |
| `Control` | `2` |
| `Shift` | `4` |
| `Meta` | `8` |

即使 `Key` 为 `Unknown`，修饰键状态也始终精确，因此 Ctrl 加一个未映射按键仍可区分。

```csharp
if (e.Modifiers.HasFlag(InputModifiers.Control) && e.Key == InputKey.Z)
{
    tree.UndoCommand.Execute(null);
    e.Handle.PreventDefault = true;
}
```

**预期结果：** Ctrl+Z 键盘事件被标志测试命中并到达树的中继；动作由宿主决定。

## MouseButton

**签名：** `enum MouseButton`

| 成员 | 值 | 含义 |
| --- | --- | --- |
| `None` | `0` | 没有按键——移动，或设备无法说明。 |
| `Left` | `1` | 主按键。 |
| `Right` | `2` | 次按键，通常是上下文菜单键。 |
| `Middle` | `3` | 中键。 |
| `XButton1` | `4` | 第一个扩展键。 |
| `XButton2` | `5` | 第二个扩展键。 |

类型名由外层命名空间限定（`VeloxDev.WorkflowSystem.MouseButton`），因为适配器文件同时导入了定义自身 `MouseButton` 的平台输入命名空间。
