# MonoBehaviour — 帧事件与线程安全

## 1. 事件载荷类型

四种载荷类型都在 `VeloxDev.TimeLine`（`Src/Core/VeloxDev.Core/TimeLine/`）：

| 类型 | 基类 | 用途 |
|---|---|---|
| `TimeLineEventArgs` | — | 抽象基类；携带 `virtual bool Handled` 标志（默认 `false`）。 |
| `FrameEventArgs` | `TimeLineEventArgs` | 传给 `Update`、`LateUpdate` 与 `FixedUpdate` 的每帧载荷。 |
| `ThreadSafeFrameEventArgs` | `FrameEventArgs` | `Handled` 读写被锁保护的变体。 |
| `TransitionEventArgs` | `TimeLineEventArgs` | 与过渡特性共享的空 sealed 载荷。 |

`FrameEventArgs` 暴露四个由通道每帧填充的只读值（`internal` 设置器）：

```csharp
partial void Update(FrameEventArgs e)
{
    Console.WriteLine($"delta   = {e.DeltaTime.TotalMilliseconds:F3} ms");  // 由时间源量得，因此已含速率
    Console.WriteLine($"elapsed = {e.TotalTime.TotalSeconds:F3} s");        // 时间源的位置，即虚拟时间
    Console.WriteLine($"fps     = {e.CurrentFPS} (target {e.TargetFPS})");
}
```

- `DeltaTime` —— 距上一个更新帧的时间，由该通道的时间源量得，因此已按其速率缩放。只有时间源没有前进时它才是 `TimeSpan.Zero`——这正是泵被告知「本帧无事可做」的方式；而速率为 `0` 时时间源被冻结，根本不会有帧带着零到来。
- `TotalTime` —— 时间源的位置，即虚拟时间。它随速率变化，并排除每一段停摆，因此只有在速率为 `1` 时才等于通道的墙钟运行时间。
- `CurrentFPS` / `TargetFPS` —— 实测帧率与配置的目标。

**预期结果：** 打印的三行每帧都在变化，并与管理器的状态查询保持一致。

## 2. `Handled` 标志 —— 短路

每帧 `Handled` 从 `false` 开始。在钩子内把它置为 `true`，会阻止循环对该阶段继续调用其它钩子：

- 在 Update 阶段，后续行为的 `Update` 被跳过，并且 —— 因为 `LateUpdate` 共享同一个帧对象 —— **该帧不再运行任何 `LateUpdate`**。
- FixedUpdate 泵为每个 tick 自建 `FrameEventArgs`，因此在 `Update` 里设置的 `Handled` 不影响 `FixedUpdate`。

```csharp
partial void Update(FrameEventArgs e)
{
    if (SomeOneShotCondition)
    {
        e.Handled = true;   // 本帧跳过其余 Update 钩子以及全部 LateUpdate
    }
}
```

**预期结果：** 标志一旦置位，在下一帧重置之前，其余行为不会再看到 `Update`（也不会有 `LateUpdate`）。

## 3. 帧对象被池化 —— 不要持有

管理器池化并复用 `FrameEventArgs` 实例（内部对象池，默认容量 50）。你的钩子收到的对象在帧末归还池中，并会在后续某帧被复用。在钩子内读取其属性是安全的；保存该对象（或把它捕获进一个比帧活得更久的闭包）会观察到被回收复用的值。若你需要在自有场景中做线程安全的 `Handled` 处理，公开的 `ThreadSafeFrameEventArgs` 子类提供受锁保护的 `Handled` 访问 —— 内置循环本身使用普通的池化 `FrameEventArgs`，`Handled` 只由泵自己写入。

**预期结果：** 你只在钩子体内使用 `e`（且循环是唯一写者），这是受支持的用法。

## 4. 线程模型

运行中的通道拥有两个泵：

- **Update 泵** 按注册顺序、在一个线程（或任务）上为每个行为派发 `Update` 再派发 `LateUpdate`；
- **FixedUpdate 泵** 每固定步长间隔（默认 16 ms）在第二个线程（或任务）上派发 `FixedUpdate`。

设计时需要留意的后果：

- `Update` 与 `FixedUpdate` 可能同时运行。二者之间的共享状态必须同步 —— 本快速入门的示例用 `Interlocked` 维护计数器，用 `lock` 同样可行。
- 钩子体运行在循环线程上，绝不运行在 UI 线程。要从 `Update` 里改动 WPF/WinUI/Avalonia 控件，需要编组到 dispatcher —— 附带的 WPF 示例正是从 `Update` 内以 `Dispatcher.Invoke(...)` 这么做（`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs`）。
- `ExecuteOnMainThread(action, channel)` 并不编组到 UI 线程。它把动作入队，在下一个 **Update 泵** 帧首、于该泵自己的线程上运行 —— 用于把工作从 FixedUpdate 线程挪到 Update 线程，而不是去够一个窗口。
- 钩子内的异常会被通道捕获（经 `Debug.WriteLine` 记录）并继续运行循环；单个坏行为不会拖垮它的邻居。
- 每个通道相互独立：行为与设置按通道划分，各通道运行自己的泵。

**预期结果：** 遵循这些规则能保证计数器精确，也让钩子能在两个泵之间无数据竞争的前提下经 dispatcher 安全更新 UI。

## 运行声明

- ⚠️ 仅静态核验 —— 类型层次、`Handled` 短路语义与线程模型转录自事件参数源文件与 `MonoBehaviourManager.cs` 中的循环体；它们在[验证与完整代码](../06_验证与完整代码/)页所述的自动化测试中被演练。
