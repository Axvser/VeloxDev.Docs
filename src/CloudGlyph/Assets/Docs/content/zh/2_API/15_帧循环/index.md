# 帧循环

`VeloxDev.TimeLine` 从命名时钟通道驱动对象的五个生命周期钩子。`[Tickable]` 生成 `ITickable` 管道；`TickManager` 拥有线程、帧率、固定步长与时间缩放。命名空间 `VeloxDev.TimeLine`。

## 类型分组

| 分组 | 类型 | 页面 |
|---|---|---|
| 契约与生成成员 | `TickableAttribute`、`ITickable`、`TimeLineEventArgs`、`FrameEventArgs`、生成的 `InitializeTickable` / `CloseTickable` / `Invoke*` / 分部钩子 | [帧驱动契约](00_帧驱动契约/index.md) |
| 管理器 | `TickManager`、`TickChannelEventArgs`、`TickBehaviorErrorEventArgs` | [帧管理器](01_帧管理器/index.md) |

## 钩子顺序

| 钩子 | 时钟 | 运行时机 |
|---|---|---|
| `Awake` | — | 每次注册一次，首帧之前 |
| `Start` | — | 每次注册一次，`Awake` 之后 |
| `Update` | 更新线程，可变增量 | 每帧一次 |
| `LateUpdate` | 更新线程，可变增量 | 同帧 `Update` 之后，除非 `Update` 置了 `Handled` |
| `FixedUpdate` | 固定线程，固定增量 | 每个欠下的固定步一次；停滞后会补发多次 |

同一帧的所有钩子复用同一个 `FrameEventArgs` 实例；钩子不得保留它。`Handled` 抑制该帧剩余行为与 `LateUpdate`，但不影响 `FixedUpdate`。

可运行程序见[帧循环快速开始](../../1_快速开始/15_帧循环/index.md)。

## 目标框架

`VeloxDev.Core` 的目标框架为 `netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0` 与 `net8.0`。在没有线程的平台（浏览器、iOS）上，`TickManager.UseAsyncLoop` 默认为 `true`，两个循环改用 `async` / `Task.Delay` 而非专用线程。没有平台检查的旧目标框架上它也默认为 `true`。
