# `TickableAttribute`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
```

源码：`Src/Core/VeloxDev.Core/TimeLine/TickableAttribute.cs`。

有两种用法会被属性规则本身排掉，因此值得明说：它只能标在**类**上（不能标在成员上；`record class` 属于类，可以），并且**不被继承** —— 基类上的 `[Tickable]` 不会把派生类放进任何通道。

### 构造函数

#### `TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1)`

**签名：**
`public TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `channel` | `string` | 生成的 `InitializeTickable()` 注册到哪个具名通道。默认 `TickManager.DEFAULT_CHANNEL`（`"default"`） |
| `fps` | `int` | 该通道的目标帧率。`-1`（默认）完全不生成帧率调用；任何 `>= 1` 的值都会让生成的注册先调 `TickManager.SetTargetFPS(fps, channel)`。除 `-1` 之外的 `<= 0` 值，在生成器 `TargetFPS >= 1` 的判定下与 `-1` 等效 |

**返回：** 一个新的特性实例。`channel` 参数存进只读属性 `Channel`，`fps` 参数存进可写属性 `TargetFPS`。

**异常：** 无。

**示例：**
```text
// 源码：Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs（第 30 行）
[Tickable(DemoChannel.Name)]
public partial class MainWindow

// DemoChannel.Name 就是 TickManager.DEFAULT_CHANNEL，且 fps 留在 -1，
// 因此窗口自己那句 SetTargetFPS(30, ...) 不会被覆盖。
```

**说明：**
- 生成器按符号而不是按名字解析该特性，所以完全限定名或别名形式同样可用（`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` 第 19-27 行）。
- 生成器在位置参数之后解析**命名参数**，所以 `[Tickable(Channel = "x")]` 与 `[Tickable("x")]` 等价；两者同时给出时命名参数胜出（`TickWriter.cs` 第 39-48 行）。
- `TargetFPS <= 0` 不会在特性里被钳制 —— 是*生成器*选择不生成那句调用。

#### 属性：`TickableAttribute.Channel`

**签名：**
`public string Channel { get; }`

**返回：** `string` —— 该行为注册到的通道名。永不为 `null`；不传参时由构造函数的默认值提供 `TickManager.DEFAULT_CHANNEL`。

**说明：**
- 只读。行为构造之后无法改通道，且生成器把通道名以字符串字面量形式在编译期烧进了生成的 `InitializeTickable()` / `CloseTickable()`。
- 生成的代码把它传给 `TickManager.RegisterBehaviour(this, "<channel>")` —— 与你手写的那句是同一个调用。

#### 属性：`TickableAttribute.TargetFPS`

**签名：**
`public int TargetFPS { get; set; }`

**返回：** `int` —— 该行为注册时要施加的目标帧率。`-1` 表示「不要动这个通道的帧率」。

**说明：**
- 与 `Channel` 不同，这个可写，所以命名参数写法 `[Tickable(TargetFPS = 60)]` 成立。
- 该值是**通道级**的目标，不是每行为的频率。同一通道上两个声明了不同 `TargetFPS` 的行为，会在注册时按注册顺序互相覆盖。

### 特性用法（已核实）

`Src/Core/VeloxDev.Core.Test/TimeLine/TickableAttributeTests.cs`：

```csharp
[TestMethod]
public void AttributeUsage_ClassOnly()
{
    var usage = (AttributeUsageAttribute?)Attribute.GetCustomAttribute(
        typeof(TickableAttribute), typeof(AttributeUsageAttribute));
    Assert.IsNotNull(usage);
    Assert.AreEqual(AttributeTargets.Class, usage.ValidOn);
    Assert.IsFalse(usage.AllowMultiple);
    Assert.IsFalse(usage.Inherited);
}
```
