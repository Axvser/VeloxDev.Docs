# 动态主题 — 控制运行中的切换

## 1. 一场切换，一条时间轴

`ThemeManager.Transition` 会创建一条 `ITimeSourceControl`，并把这一场切换的**每一个**目标都锚定在它上面。因此每场切换恰好只有一条 transport，而且就是过渡动画本来就暴露的那一条 —— 于是用普通的 `Transition.*` 表面去寻址任意一个已注册目标，就能移动整场切换。一次 `Transition.Pause(tile)` 会同时冻结全部一千个块；不需要额外的构造，也没有主题专用的控制 API 要学。

这条 run 是普通的过渡 run，也是「effect 被原样使用」的原因：`IsAutoReverse`、`LoopTime` 这类标志会被真正遵守，而不是被忽略。`ThemeTransitionTests.Switch_HonoursAutoReverseAndLoopTime` 用 `IsAutoReverse = true` 与 `LoopTime = 1` 做切换，最终停在**起点**值上，因为最后一程是反向程 —— 这条断言本身就是标志仍然生效的证据。

**预期结果：** 针对单个目标的一次控制调用可在所有目标上观察到。由 `ThemeTransitionTests.Switch_EveryTargetIsAnchoredToTheSameTimeline` 锁定 —— 它暂停目标 A，并断言目标 B 报告 `IsPaused`。

## 2. 控制面

`Transition` 是适配器类型（命名空间 `VeloxDev.TransitionSystem`）；以下成员是 `TransitionCore` 上的静态方法，每一个都接受可选的 `IncludeMutual` / `IncludeNoMutual` 标志：

| 调用 | 对一场主题切换的效果 |
|---|---|
| `Transition.Position(target)` | 切换已运行到何处（`TimeSpan`） |
| `Transition.Cycle(target)` | 第几程 |
| `Transition.IsPaused(target)` / `Transition.Rate(target)` | 当前 transport 状态 |
| `Transition.Pause(target)` / `Transition.Resume(target)` | 冻结 / 继续整场切换 |
| `Transition.SetRate(target, 0.25)` | 以不同倍率播放整场切换 |
| `Transition.Seek(target, position)` | 把整场切换拖到某个位置 |
| `Transition.Exit(target, IncludeMutual: true, IncludeNoMutual: true)` | 取消各 run，并把值留在原地 |

规模示例的工具条正是接在这些调用上，而且每个处理器只寻址第一个块：

```csharp
private void Act(Action<ThemeTile> operation)
{
    if (_tiles.Count == 0) return;

    operation(_tiles[0]);
    UpdateLive();
}

private void OnTogglePause(object sender, RoutedEventArgs e) => Act(tile =>
{
    if (Transition.IsPaused(tile)) Transition.Resume(tile);
    else Transition.Pause(tile);
});

private void OnSeekHalf(object sender, RoutedEventArgs e)
    => Act(tile => Transition.Seek(tile, TimeSpan.FromMilliseconds(_effect.Duration.TotalMilliseconds / 2)));

private void OnStop(object sender, RoutedEventArgs e)
    => Act(tile => Transition.Exit(tile, IncludeMutual: true, IncludeNoMutual: true));
```

来源：`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的 `Act`、`OnTogglePause`、`OnSeekHalf`、`OnStop`（Avalonia 示例的同名处理器形参为 `object?`，其余相同）。

`Seek` 拖过一程的末尾并不会被悄悄钳掉：一程只有一个终点，因此这一程会跑到头，并精确落在声明的值上 —— `ThemeTransitionTests.Switch_SeekIsReachableAndFinishesThePass` 在一场 30 秒的切换上 seek 到 31 秒，并断言值等于声明的终值。`Exit` 则相反：它把属性留在冻结处，而且被取消的 run 永远不会落地，所以 `ThemeManager.Current` 仍指向旧主题。

**预期结果：** 在此暂停会把每个已映射属性冻结在同一位置；seek 会把它们一起移动；`Exit` 让它们停在半途且 `Current` 不变。

## 3. 同样的东西放到规模上

`Examples/Theme/WPF/Demo` 与 `Examples/Theme/Avalonia/Demo` 是规模示例：默认一千个 `ThemeTile` 元素 —— 一个 26×26 的 `Border`，映射 `Background` 与 `BorderBrush`，并在构造函数里完成自注册 —— 再加上窗口自身作为一个参与主题的元素，跑在 3 秒的 effect 上。

它们的存在就是为了让共享时间轴变得可见。工具条就是上面的控制面；`Status` 报告元素数、切换是落地还是被中断、准备耗时、总耗时、帧数、每目标帧数、分配量与 CPU 时间；一个 100 毫秒的计时器只读取**第一个**块的实时 transport 状态：

```csharp
var tile = _tiles[0];
Live.Text = string.Format(
    "pos {0:F0} ms · cycle {1} · paused {2} · rate {3:F2} · Current {4}",
    Transition.Position(tile).TotalMilliseconds,
    Transition.Cycle(tile),
    Transition.IsPaused(tile),
    Transition.Rate(tile),
    ThemeManager.Current.Name);
```

来源：`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的 `UpdateLive`。切换运行期间读这一行：它读的那个块并不特殊，这正是重点 —— 它报告的位置、程数、暂停标志与倍率，就是整场切换的。

同一个示例还有一个无头模式，会以 1、50、200、1000 个元素重复该场景并写出计时表；见[验证与完整代码](../../04_验证与完整代码/index.md)。

**预期结果：** 1000 个元素时，暂停按钮把所有块冻结在同一位置，实时读数持续报告那个共享位置。
