# 视口恢复

新挂载的表面必须在树的已保存滚动位置打开，而不是原点。`SurfaceViewportRestoreCore` 拥有状态机；适配器只提供平台上的延迟执行与两次写入。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## SurfaceViewportRestoreCore

**签名：** `sealed class SurfaceViewportRestoreCore`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `HasPendingRestore` | `bool` | 是否仍有已捕获、等待恢复的位置。 |
| `Capture(ITreeComponent? tree)` | `void` | 当 `tree` 与上次捕获的树不同时捕获 `tree.Layout.ViewportOffset`。null 树被忽略。 |
| `Schedule(ISurfaceViewportRestoreHost host, Action? afterRestore = null)` | `void` | 有待恢复位置时安排一次延迟恢复。已排队时再次调用不做事。宿主为 null 时抛 `ArgumentNullException`。 |

捕获以树实例为键，因此同一棵树反复刷新绝不会把用户移回原位。`Capture` 必须在表面把当前视口写回 `Layout.ViewportOffset` **之前**运行，否则保存的位置会被原点覆盖。

`Schedule` 交给宿主的回调依次：

1. 清除 `isQueued`。
2. 当 `host.IsRestoreEnabled` 为 false 时不消费待恢复位置并返回，让下一次刷新重试。
3. 清除待恢复位置，并按 `host.HorizontalMaximum` / `host.VerticalMaximum` 钳制后应用捕获的偏移。
4. 运行 `afterRestore`。

## ISurfaceViewportRestoreHost

**签名：** `interface ISurfaceViewportRestoreHost`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `IsRestoreEnabled` | `bool` | 表面是否仍挂载且滚动容器已解析。 |
| `HorizontalMaximum` / `VerticalMaximum` | `double` | 当前滚动上限。 |
| `ApplyOffset(double horizontalOffset, double verticalOffset)` | `void` | 写入两个偏移。 |
| `DeferRestore(Action restore)` | `void` | 在平台完成新挂载树的布局之后调度回调。 |

布局何时完成由适配器决定；是否恢复、恢复什么留在 Core。

```csharp
var restore = new SurfaceViewportRestoreCore();

// 在表面写入第一个视口之前
restore.Capture(tree);

// 命名部件解析之后
restore.Schedule(host, afterRestore: () => SurfaceMetricsPush.PushViewport(metrics, tree));
```

**预期结果：** 带有非零 `Layout.ViewportOffset` 的树在该偏移打开；没有的树停在原点。同一棵树第二次刷新不会移动用户。
