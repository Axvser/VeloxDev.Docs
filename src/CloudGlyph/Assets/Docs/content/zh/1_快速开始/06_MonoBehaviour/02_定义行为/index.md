# MonoBehaviour — 定义行为

## 1. 特性

行为是任何带 `VeloxDev.TimeLine.MonoBehaviourAttribute` 标注的 `partial` 类。该特性有两个可选参数（`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourAttribute.cs`）：

- `channel` —— 行为注册到的具名通道。默认是 `"default"` 通道（`MonoBehaviourManager.DEFAULT_CHANNEL`）。同一通道的所有行为共享两个帧泵。
- `fps` —— 注册时请求的目标 FPS。默认 `-1` 表示“沿用通道现有设置”；`1` 及以上会令生成器在注册时额外调用 `MonoBehaviourManager.SetTargetFPS(fps, channel)`。

特性仅作用于类、不可继承、不可重复。

```csharp
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
}
```

**预期结果：** 该类无需手写接口实现即可编译 —— 生成器把它变成 `IMonoBehaviour`。

## 2. 生成器生成了什么

生成器（`Src/Generators/VeloxDev.Core.Generator/Writers/MonoWriter.cs`）在同一命名空间中合成该类的另一半。生成的 partial：

- 实现 `VeloxDev.MonoBehaviour.IMonoBehaviour`，因此类现在拥有桥接成员 `InitializeMonoBehaviour()`、`CloseMonoBehaviour()`、`InvokeAwake()`、`InvokeStart()`、`InvokeUpdate(FrameEventArgs)`、`InvokeLateUpdate(FrameEventArgs)`、`InvokeFixedUpdate(FrameEventArgs)`；
- 声明循环通过该桥接调用的五个 **`partial void` 生命周期钩子**：

```csharp
partial void Awake();
partial void Start();
partial void Update(FrameEventArgs e);
partial void LateUpdate(FrameEventArgs e);
partial void FixedUpdate(FrameEventArgs e);
```

- 添加 `public void InitializeMonoBehaviour()` 用于注册实例：它调用 `MonoBehaviourManager.RegisterBehaviour(this, "game")`，并在 `fps >= 1` 时先调用 `MonoBehaviourManager.SetTargetFPS(fps, "game")`；
- 添加 `public void CloseMonoBehaviour()`，它调用 `MonoBehaviourManager.UnregisterBehaviour(this, "game")`。

不存在 `[Update]` 特性，也没有可重写的虚方法 `OnFrame`：你直接实现 `partial void` 钩子（有体或无体，签名与生成的一致）。未实现的钩子只是空操作。

## 3. 注册实例

生成器不会发明构造函数，因此你必须自行注册每个实例 —— 通常在自己的构造函数中：

```csharp
public FrameCounter() => InitializeMonoBehaviour();
```

`InitializeMonoBehaviour()` 只是把注册入队。钩子会在运行中的通道于帧首清空加入队列时触发：

- `Awake()` 与 `Start()` 各运行一次 —— 行为首次被循环拾取时；
- `Update(FrameEventArgs)` 每个更新帧运行一次；
- `LateUpdate(FrameEventArgs)` 每个更新帧运行一次，紧随所有行为的 `Update`；
- `FixedUpdate(FrameEventArgs)` 在独立的固定步长泵上运行（默认每 16 ms 一次）。

**预期结果：** 构造 `FrameCounter` 会把它注册到 `"game"` 通道；由于通道尚未运行，`Awake` / `Start` 暂不会被调用（见[运行与配置循环](../03_运行与配置循环/)页）。

## 4. 一个完整的最小行为

```csharp
using System;
using System.Threading;
using VeloxDev.TimeLine;

namespace MonoQuickStart;

[MonoBehaviour(channel: "game", fps: 60)]
public partial class FrameCounter
{
    public long UpdateCount;
    public long FixedUpdateCount;

    public FrameCounter() => InitializeMonoBehaviour();   // 把当前实例注册到 "game"

    partial void Awake() => Console.WriteLine("[Awake] behaviour registered");

    partial void Start() => Console.WriteLine("[Start] loop is running");

    partial void Update(FrameEventArgs e)
    {
        Interlocked.Increment(ref UpdateCount);
    }

    partial void LateUpdate(FrameEventArgs e)
    {
    }

    partial void FixedUpdate(FrameEventArgs e)
    {
        Interlocked.Increment(ref FixedUpdateCount);
    }
}
```

因为 `Update` 与 `FixedUpdate` 运行在不同的循环线程上，`Interlocked` 保证计数器正确。该类也说明嵌套/有基类的层次完全没问题 —— WPF 示例同样给 `MainWindow : Window` 与嵌套的 `private partial class` 组件打 `[MonoBehaviour]`（`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs`）。

**预期结果：** 该类加上一个调用 `MonoBehaviourManager.Start("game")` 的控制台宿主，会各打印一次两个括号行，并在通道运行期间持续增长 `UpdateCount` / `FixedUpdateCount`。

## 运行声明

- ⚠️ 仅静态核验 —— 钩子签名与生成的成员形态转录自 `MonoWriter.cs` 与 `IMonoBehaviour` 接口，计数器行为模式转录自 WPF 示例；编写本页时未运行编译。完整程序在[验证与完整代码](../06_验证与完整代码/)页编译并运行。
