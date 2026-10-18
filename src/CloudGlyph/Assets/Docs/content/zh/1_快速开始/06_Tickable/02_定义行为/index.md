# 定义行为

一个行为就是一个带 `[Tickable]` 的 `partial` 类。特性选择**通道**，并可选指定该通道的**目标帧率**。类的其余部分都是普通 C#。

## 1. 特性

`Src/Core/VeloxDev.Core/TimeLine/TickableAttribute.cs`：

```csharp
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; } = channel;
    public int TargetFPS { get; set; } = fps;
}
```

由此有三点容易搞错：

- **只作用于类，且不被继承。** `AllowMultiple = false`、`Inherited = false`，所以派生类**不会**继承基类上的 `[Tickable]`。每个想要钩子的类都自己带特性。
- **通道是字符串。** 默认 `TickManager.DEFAULT_CHANNEL`，即字面量 `"default"`。
- **`fps` 是目标帧率，不是倍率；`-1` 表示「不要碰通道」。** 值 `>= 1` 时生成的注册还会调用 `TickManager.SetTargetFPS(fps, channel)`；值为 `-1` 时完全不生成帧率调用。示例中的 `DemoChannel.Name` 就是 `TickManager.DEFAULT_CHANNEL`，类声明为 `[Tickable(DemoChannel.Name)]`（`MainWindow.Hooks.cs` 第 23 行）—— 只给通道，`fps` 留在 `-1`，所以窗口自己的 `SetTargetFPS(30, ...)` 不会被覆盖。

## 2. 类

```csharp
using VeloxDev.TimeLine;

[Tickable("demo", 60)]
public partial class BouncingBall
{
    partial void Awake() => Console.WriteLine("awake");
    partial void Start() => Console.WriteLine("start");
    partial void Update(FrameEventArgs e) { }
    partial void LateUpdate(FrameEventArgs e) { }
    partial void FixedUpdate(FrameEventArgs e) { }
}
```

**预期结果：** `dotnet build` 成功。生成器已为 `BouncingBall` 添加了第二个声明，实现 `ITickable`。

## 3. 生成器写了什么

`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs` 向编译追加一个 partial 声明。`TickWriter.GenerateBody`（第 74-127 行）生成如下内容（省略 `global::` 前缀）：

```csharp
public void InitializeTickable()
{
    global::VeloxDev.TimeLine.TickManager.SetTargetFPS(60, "demo");
    global::VeloxDev.TimeLine.TickManager.RegisterBehaviour(this, "demo");
}

public void CloseTickable()
{
    global::VeloxDev.TimeLine.TickManager.UnregisterBehaviour(this, "demo");
}

public void InvokeAwake()        { Awake(); }
public void InvokeStart()        { Start(); }
public void InvokeUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)      { Update(e); }
public void InvokeLateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e)  { LateUpdate(e); }
public void InvokeFixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e) { FixedUpdate(e); }

partial void Awake();
partial void Start();
partial void Update(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void LateUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
partial void FixedUpdate(global::VeloxDev.TimeLine.FrameEventArgs e);
```

两点值得记住：

- **只有 `fps >= 1` 时才生成 `SetTargetFPS` 那一行。** 写成 `[Tickable("demo")]` 时该行不存在，通道保持原有帧率。
- **你只需要调用 `InitializeTickable()` 与 `CloseTickable()`。** 没有别的东西替你调用它们。注册是一次*入队*，所以 `InitializeTickable()` 可以在通道启动之前调用 —— 排空发生在通道第一帧之前。

## 4. 五个钩子与运行时机

| 钩子 | 运行在 | 频率 |
|---|---|---|
| `Awake` | update 泵，注册队列排空时 | 每次注册一次 |
| `Start` | update 泵，紧接 `Awake` | 每次注册一次 |
| `Update` | update 泵 | 每帧 |
| `LateUpdate` | update 泵 | 每帧，在所有行为的 `Update` 之后 |
| `FixedUpdate` | fixed-update 泵 | 每个步长（默认 16 ms），与 update 泵并发 |

`Awake` 与 `Start` 在**第一帧帧体之前**、于 update 线程上运行，来自 `ProcessAddedBehaviors`（`TickManager.cs` 第 787-803 行）：

```csharp
var wrapper = _wrapperPool.Get();
wrapper.Reset(behavior, Interlocked.Increment(ref _instanceCounter));

_behaviors[RuntimeHelpers.GetHashCode(behavior)] = wrapper;
SafeExecute(behavior.InvokeAwake);
SafeExecute(behavior.InvokeStart);
```

因为该代码块在帧采样之前被排空，在 `Awake` 中读取 `TickManager.TotalFrames(channel)` 会看到**第一帧之前**的计数 —— WPF 示例显示的 `SimState.AwakeFrameOrdinal` 就是这条证据。

**预期结果：** 类能编译；你能指出自己拥有的五个钩子函数体，以及要调用的两个生成方法。

## 说明

- 钩子是 `partial void`，未实现的会被编译器移除 —— 不需要写空重写，跳过的钩子也没有开销。
- `InvokeUpdate` 等是 `ITickable` 的表面，不是用户 API。调用 `InitializeTickable` / `CloseTickable`，其余交给泵。
- 钩子抛出的异常按行为逐个捕获并写入 `Debug.WriteLine`（`ExecuteBehaviorsUpdateSync`，`TickManager.cs` 第 691-704 行）。抛异常的钩子不会停下循环，在 Release 构建中也悄无声息。
