# `ITickable`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public interface ITickable
{
    void InitializeTickable();
    void CloseTickable();
    void InvokeAwake();
    void InvokeStart();
    void InvokeUpdate(FrameEventArgs e);
    void InvokeLateUpdate(FrameEventArgs e);
    void InvokeFixedUpdate(FrameEventArgs e);
}
```

源码：`Src/Core/VeloxDev.Core/Interfaces/Tickable/ITickable.cs`。

这就是原名 `IMonoBehaviour` 的接口，它所在的命名空间也由 `VeloxDev.MonoBehaviour` 改成了 `VeloxDev.TimeLine` —— 因此旧的 `using VeloxDev.MonoBehaviour;` 已经编不过。成员名 `InitializeTickable` / `CloseTickable` 同样是新的（旧名 `InitializeMonoBehaviour` / `CloseMonoBehaviour`）。

**你几乎不需要手写实现。** 源生成器会为任何带 `[Tickable]` 的 `partial` 类写出全部七个成员；`TickManager.RegisterBehaviour` 之所以接受这个接口，只是因为通道就是从这条形状上派发的。手写实现是合法的，测试在需要最小行为时就是这么做的。

| 成员 | 由谁调用 | 典型函数体 |
|---|---|---|
| `InitializeTickable()` | 你 | `TickManager.RegisterBehaviour(this, "<通道>")` —— 生成的版本在特性给了 `fps` 时还会先调 `SetTargetFPS` |
| `CloseTickable()` | 你 | `TickManager.UnregisterBehaviour(this, "<通道>")` |
| `InvokeAwake()` | update 泵的注册排空 | 调用你的 `Awake` |
| `InvokeStart()` | 同一个排空过程，紧随 `InvokeAwake()` | 调用你的 `Start` |
| `InvokeUpdate(FrameEventArgs)` | update 泵，每帧一次 | 调用你的 `Update` |
| `InvokeLateUpdate(FrameEventArgs)` | update 泵，每帧一次，在所有行为的 `InvokeUpdate` 之后 | 调用你的 `LateUpdate` |
| `InvokeFixedUpdate(FrameEventArgs)` | fixed-update 泵，每个欠下的步一次 | 调用你的 `FixedUpdate` |

#### `ITickable.InitializeTickable`

**签名：**
`void InitializeTickable()`

**返回：** `void`。

**说明：**
- **循环从不调用它。** 它是你进入注册的入口，不是框架回调；知道通道名的唯一地方就是生成的那份实现。
- 它注册到哪个通道来自 `[Tickable]` 特性的 `Channel`，在编译期以字符串字面量烧进去 —— 实例本身并不携带通道。

#### `ITickable.CloseTickable`

**签名：**
`void CloseTickable()`

**返回：** `void`。

**说明：**
- 也从不被循环调用。注销是静默的：泵只是停止派发，行为上没有任何「已关闭」钩子。
- `CloseTickable()` 之后实例仍然可用，可以再次注册 —— 那会在新的 wrapper 上重跑 `InvokeAwake` 与 `InvokeStart`。

#### `ITickable.InvokeAwake`

**签名：**
`void InvokeAwake()`

**返回：** `void`。

**说明：**
- 每次注册调用一次，发生在 update 泵的注册排空期间（`ProcessAddedBehaviors`，`TickManager.cs` 第 785-801 行），**早于第一帧帧体**。
- 被 `SafeExecute` 包住（第 939-942 行），所以此处抛异常只会写进 `Debug.WriteLine`，不会阻止 `InvokeStart` 或循环。
- 运行在 update 线程，不是调用方线程：`RegisterBehaviour` 只是入队。

#### `ITickable.InvokeStart`

**签名：**
`void InvokeStart()`

**返回：** `void`。

**说明：**
- 在同一次排空中紧接 `InvokeAwake` 调用，同一帧内。
- 同样的 `SafeExecute` 保护，同样的线程。

#### `ITickable.InvokeUpdate`

**签名：**
`void InvokeUpdate(FrameEventArgs e)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `e` | `FrameEventArgs` | 本帧的池化参数。调用发生时 `e.Handled` 为 `false`；置位它会中止本帧阶段的其余部分 |

**返回：** `void`。

**说明：**
- 每帧对每个已注册行为调用一次，运行在通道的 update 线程上，按注册顺序。
- 派发循环是在每个行为**之前**检查 `frameArgs.Handled` 与取消令牌（`ExecuteBehaviorsUpdateSync`，第 689-702 行），所以置位 `Handled` 的那个行为不会被跳过 —— 被跳过的是它之后的一切。
- 异常按行为逐个捕获并写进 `Debug.WriteLine`；循环继续处理下一个行为。

#### `ITickable.InvokeLateUpdate`

**签名：**
`void InvokeLateUpdate(FrameEventArgs e)`

**返回：** `void`。

**说明：**
- 是同一个业务数组上的另一个循环，有自己的 `Handled` 检查 —— 这就是为什么在 `InvokeUpdate` 里置 `Handled` 会跳过该帧**整个** late 阶段，而不只是本行为的 late 回调。
- 运行在 update 线程上，在该帧所有行为的 `InvokeUpdate` 之后。

#### `ITickable.InvokeFixedUpdate`

**签名：**
`void InvokeFixedUpdate(FrameEventArgs e)`

**返回：** `void`。

**说明：**
- 运行在 fixed-update 线程上，与 `InvokeUpdate` / `InvokeLateUpdate` **并发**。任何被两者触碰的字段都要自己做同步。
- 每个欠下的步各自拿到一个 `FrameEventArgs`，逐步构造并立刻归还池中（`FixedUpdateLoop`，第 483-493 行），所以 `InvokeUpdate` 里置位的 `Handled` 永远到不了这个泵。
- 一次停摆会以连续多次调用的形式补还，上限是采样器每次调用的步数上限。

## 手写实现

`Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs` 第 45-67 行 —— 没有生成器参与时测试用的最小合法实现：

```csharp
private sealed class PushCounter : ITickable
{
    private int _updates;
    private int _fixedUpdates;

    public int Updates => Volatile.Read(ref _updates);

    public int FixedUpdates => Volatile.Read(ref _fixedUpdates);

    public void InitializeTickable() { }

    public void CloseTickable() { }

    public void InvokeAwake() { }

    public void InvokeStart() { }

    public void InvokeUpdate(FrameEventArgs e) => Interlocked.Increment(ref _updates);

    public void InvokeLateUpdate(FrameEventArgs e) { }

    public void InvokeFixedUpdate(FrameEventArgs e) => Interlocked.Increment(ref _fixedUpdates);
}
```

注意测试是怎么用它的 —— `InitializeTickable()` 留空，注册直接走 `TickManager.RegisterBehaviour(counter, channel)`。这才是诚实的分工：`InitializeTickable` 存在的唯一意义，是让生成的类有个地方放通道名。
