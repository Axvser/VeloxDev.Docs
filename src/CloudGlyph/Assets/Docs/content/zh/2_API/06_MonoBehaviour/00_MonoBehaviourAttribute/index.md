# MonoBehaviour — `MonoBehaviourAttribute`

`[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]`

```csharp
public sealed class MonoBehaviourAttribute(string channel = MonoBehaviourManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; }
    public int TargetFPS { get; set; }
}
```

把 `partial` 类标记为帧驱动行为。源生成器读取该特性并生成 `IMonoBehaviour` 桥接（`MonoWriter.cs` 第 13-50、80-121 行）。

#### `MonoBehaviourAttribute.MonoBehaviourAttribute`（构造函数）

**签名：**
`public MonoBehaviourAttribute(string channel = MonoBehaviourManager.DEFAULT_CHANNEL, int fps = -1)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `channel` | `string` | 该行为注册到的命名循环通道。默认 `"default"`。 |
| `fps` | `int` | 注册时应用的目标帧率；`-1` 表示沿用通道现有设置。 |

**返回：** `MonoBehaviourAttribute`

**示例：**
```text
// 出处：Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs（第 8 行）
[MonoBehaviour]
public partial class MainWindow : Window { ... }
```

**说明：**
- 仅适用于类，不可继承，不可重复（由 `MonoBehaviourAttributeTests.AttributeUsage_ClassOnly` 验证）。

#### `MonoBehaviourAttribute.Channel`

**签名：**
`public string Channel { get; }`

**返回：** `string` — 该行为对应的命名通道。

**说明：**
- 只读；生成器据此生成 `RegisterBehaviour(this, "channel")`（`MonoWriter.cs` 第 76-84 行）。

#### `MonoBehaviourAttribute.TargetFPS`

**签名：**
`public int TargetFPS { get; set; }`

**返回：** `int` — `-1` 表示「沿用通道设置」；任何 `>= 1` 的值会在注册前通过 `MonoBehaviourManager.SetTargetFPS` 应用。

**说明：**
- 可通过命名参数设置：`[MonoBehaviour(channel: "game", fps: 60)]`。
