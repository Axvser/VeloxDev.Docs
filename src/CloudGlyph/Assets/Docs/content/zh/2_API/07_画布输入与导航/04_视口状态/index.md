# 视口状态

表面把当前状态作为不可变记录交给覆盖层，并在布局稳定后恢复保存的滚动位置。两者都是 Core 类型，因此每家适配器喂给覆盖层的是同一种数据包。

## SurfaceViewport

```csharp
public sealed record SurfaceViewport(
    ITreeComponent Tree,
    double ScrollLeft,
    double ScrollTop,
    double ViewportWidth,
    double ViewportHeight,
    double ContentOffsetX,
    double ContentOffsetY);
```

位置记录，因此还自带 `Deconstruct`、值相等与 `ToString`。它镜像的正是 `IWorkflowGridDecorator` 与 `IWorkflowMinimapOverlay` 收到的内容。

## SurfaceCanvas

```csharp
public sealed record SurfaceCanvas(double Width, double Height);
```

传给表面内容片段的计算画布尺寸，子层可以据此与画布同尺寸。

## SurfaceViewportFeed

```csharp
public sealed class SurfaceViewportFeed
{
    public SurfaceViewport? Current { get; private set; }
    public event Action<SurfaceViewport>? Changed;
    public void Publish(SurfaceViewport viewport);
}
```

| 成员 | 说明 |
|---|---|
| `Current` | 最近一次发布的快照；首次发布前为 `null`。 |
| `Changed` | 每次 `Publish` 时以新快照触发。 |
| `Publish` | 保存快照并触发 `Changed`。 |

Feed 让覆盖层订阅视口变化，而不必回读表面或触发整面重绘。Razor 表面把它暴露为级联参数；其他适配器通过 `SurfaceMetricsPush` 推送同样的值。

## ISurfaceViewportRestoreHost

```csharp
public interface ISurfaceViewportRestoreHost
{
    bool IsRestoreEnabled { get; }
    double HorizontalMaximum { get; }
    double VerticalMaximum { get; }
    void ApplyOffset(double horizontalOffset, double verticalOffset);
    void DeferRestore(Action restore);
}
```

| 成员 | 说明 |
|---|---|
| `IsRestoreEnabled` | 宿主开关；`false` 取消待执行的恢复。 |
| `HorizontalMaximum` / `VerticalMaximum` | 用于钳制恢复偏移的实时最大值。 |
| `ApplyOffset` | 写入恢复的偏移。 |
| `DeferRestore` | 把恢复推迟到宿主可执行时。 |

## SurfaceViewportRestoreCore

```csharp
public sealed class SurfaceViewportRestoreCore
```

| 成员 | 说明 |
|---|---|
| `HasPendingRestore` | 是否已捕获但尚未应用恢复。 |
| `Capture(ITreeComponent? tree)` | `HasViewportRestore` 为真时，每棵不同的树只捕获一次。要在当前视口被写回之前运行。 |
| `Schedule(ISurfaceViewportRestoreHost host, Action? afterRestore = null)` | 最多排队一次恢复；执行时重新检查待执行状态与宿主开关，按实时最大值钳制，然后调用 `afterRestore`。宿主为 null 时抛 `ArgumentNullException`。 |

顺序是：加载时捕获保存的偏移，让表面完成首次布局，然后调度。第一次执行前再次 `Schedule` 不会重复排队。

## 说明

- 恢复是一个一次性的布局后动作，不是持续同步；之后的滚动仍由用户控制。
- 捕获与调度分开，是因为首次布局会覆盖布局里的偏移。
- `Capture` 对同一棵树幂等。
