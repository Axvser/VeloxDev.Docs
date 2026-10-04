# 02 · 定义行为

一个「行为」就是一个带 `[Tickable]` 的 `partial` 类。特性选定**通道**，并可选地指定该通道的**目标帧率**。类的其余部分就是最普通的 C#。

## 1. 特性本身

`Src/Core/VeloxDev.Core/TimeLine/TickableAttribute.cs`：

```csharp
[AttributeUsage(AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
public sealed class TickableAttribute(string channel = TickManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; } = channel;
    public int TargetFPS { get; set; } = fps;
}
```

从这个声明可以推出三件事，而这三件事都很容易搞错：

- **只能标在类上，不能标在成员上。** `AllowMultiple = false` 且 `Inherited = false`，所以派生类**不会**继承基类的 `[Tickable]`。每个想要钩子的类都要自己带上该特性。
- **通道是一个字符串。** 默认值 `TickManager.DEFAULT_CHANNEL`，即字面量 `"default"`。
- **`fps` 是目标帧率，不是倍率；`-1` 表示「别动这个通道的帧率」。** 当值 `>= 1` 时，生成的注册代码还会调用 `TickManager.SetTargetFPS(fps, channel)`；为 `-1` 时一行帧率调用都不会生成。演示中 `DemoChannel.Name` 就是 `TickManager.DEFAULT_CHANNEL`，类声明为 `[Tickable(DemoChannel.Name)]` —— 只给通道，`fps` 留在 `-1`，这样窗口自己那句 `SetTargetFPS(30, ...)` 不会被覆盖。见 `Examples/Tickable/WPF/Demo/MainWindow.Hooks.cs` 第 30 行。

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

**预期结果：** `dotnet build` 成功。生成器已经往编译里加了一份实现 `ITickable` 的 `BouncingBall` 分部声明。

## 3. 生成器写了什么

生成器（`Src/Generators/VeloxDev.Core.Generator/Writers/TickWriter.cs`）向编译追加一个 partial 类。去掉 `global::` 前缀后，`TickWriter.GenerateBody`（第 69-122 行）生成的内容是：

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

有两点值得记住：

- **那句 `SetTargetFPS` 只在 `fps >= 1` 时出现。** 写成 `[Tickable("demo")]` 时它不存在，通道保持原有帧率。
- **你只会调用 `InitializeTickable()` 与 `CloseTickable()` 这两个方法。** 没有别的东西替你调用它们。注册本质是一次**入队**，所以 `InitializeTickable()` 可以在通道启动之前调用 —— 队列会在通道的第一帧被排空。

## 4. 五个钩子与它们的时机

| 钩子 | 运行线程 | 频率 |
|---|---|---|
| `Awake` | Update 泵，注册队列的首次排空 | 每次注册一次 |
| `Start` | Update 泵，紧随 `Awake` | 每次注册一次 |
| `Update` | Update 泵 | 每帧 |
| `LateUpdate` | Update 泵 | 每帧，在所有行为的 `Update` 之后 |
| `FixedUpdate` | FixedUpdate 泵 | 每步间隔一次（默认 16 ms），与 Update 泵并发 |

`Awake` 与 `Start` **在第一帧帧体之前**运行，位置是 Update 线程上的 `ProcessAddedBehaviors`（`TickManager.cs` 第 785-801 行）：

```csharp
var wrapper = _wrapperPool.Get();
wrapper.Reset(behavior, Interlocked.Increment(ref _instanceCounter));

_behaviors[RuntimeHelpers.GetHashCode(behavior)] = wrapper;
SafeExecute(behavior.InvokeAwake);
SafeExecute(behavior.InvokeStart);
added = true;
```

由于这段排空发生在采样之前，在 `Awake` 里读 `TickManager.TotalFrames(channel)` 得到的仍是**第一帧之前**的计数 —— WPF 演示把它显示成生命周期证据（`SimState.AwakeFrameOrdinal`）。

**预期结果：** 类能编译，你能指出五个自己拥有的钩子函数体，和两个自己调用的生成方法。

## 说明

- 钩子是 `partial void`，没实现的那个会被编译器整个移除 —— 不需要写空重写，跳过的也没有任何开销。
- `InvokeUpdate` 之类是 `ITickable` 的表面，不是用户 API。你只调用入口（`InitializeTickable` / `CloseTickable`），其余交给泵。
- 钩子里抛出的异常会按行为逐个捕获并写进 `Debug.WriteLine`（见 `ExecuteBehaviorsUpdateSync`，`TickManager.cs` 第 689-702 行）。抛异常的钩子既不会停下循环，也不会在 Release 构建里出现在控制台上。
