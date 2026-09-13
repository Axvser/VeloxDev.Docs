# Dynamic Theme — Control a Switch in Flight

## 1. One switch, one timeline

`ThemeManager.Transition` creates a single `TransitionTimeline` and anchors **every** target of that switch to it. There is therefore exactly one transport per switch, and it is the same transport the TransitionSystem already exposes — so addressing any one registered target with the ordinary `Transition.*` surface moves the whole switch. One `Transition.Pause(tile)` freezes all thousand tiles; there is nothing extra to build and no theme-specific control API to learn.

The run being a normal transition run is also why the effect is used as given: flags such as `IsAutoReverse` and `LoopTime` are honoured rather than ignored. `ThemeTransitionTests.Switch_HonoursAutoReverseAndLoopTime` switches with `IsAutoReverse = true` and `LoopTime = 1` and settles on the **start** value, because the last pass is a reverse one — the assertion is the evidence that the flags still apply.

**Expected result:** a control call aimed at one target is observable on all of them. Pinned by `ThemeTransitionTests.Switch_EveryTargetIsAnchoredToTheSameTimeline`, which pauses target A and asserts that target B reports `IsPaused`.

## 2. The control surface

`Transition` is the adapter type (namespace `VeloxDev.TransitionSystem`); these members are the statics on `TransitionCore`, and every one of them takes the optional `IncludeMutual` / `IncludeNoMutual` flags:

| Call | Effect on a theme switch |
|---|---|
| `Transition.Position(target)` | how far the switch has run, as a `TimeSpan` |
| `Transition.Cycle(target)` | the pass index |
| `Transition.IsPaused(target)` / `Transition.Rate(target)` | the current transport state |
| `Transition.Pause(target)` / `Transition.Resume(target)` | freeze / continue the whole switch |
| `Transition.SetRate(target, 0.25)` | play the whole switch at a different rate |
| `Transition.Seek(target, position)` | drag the whole switch to a position |
| `Transition.Exit(target, IncludeMutual: true, IncludeNoMutual: true)` | cancel the runs and leave the values where they are |

The scale demo wires its toolbar to exactly these calls, and each handler addresses the first tile only:

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

Source: `Examples/Theme/WPF/Demo/MainWindow.xaml.cs`, members `Act`, `OnTogglePause`, `OnSeekHalf`, `OnStop` (the Avalonia demo's handlers take `object?` and are otherwise the same).

`Seek` past the end of the pass is not clamped into nothing: one pass has exactly one endpoint, so the pass runs out and the switch lands precisely on the declared value — `ThemeTransitionTests.Switch_SeekIsReachableAndFinishesThePass` seeks to 31 s on a 30 s switch and asserts the value equals the declared end value. `Exit`, by contrast, leaves the properties wherever they froze, and because a cancelled run never lands, `ThemeManager.Current` still names the old theme.

**Expected result:** pausing here freezes every mapped property at the same position; seeking moves them all together; `Exit` stops them mid-flight and leaves `Current` unchanged.

## 3. The same thing at scale

`Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo` are the scale demos: a thousand `ThemeTile` elements by default — a 26×26 `Border` that maps `Background` and `BorderBrush` and registers itself from its constructor — plus the window itself as one more themed element, on a 3-second effect.

They exist to make the shared timeline visible. The toolbar is the control surface above; `Status` reports the element count, whether the switch landed or was interrupted, preparation time, total time, frame count, per-target frames, allocations and CPU time; and a 100 ms ticker prints the live transport state of the **first** tile only:

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

Source: `Examples/Theme/WPF/Demo/MainWindow.xaml.cs`, member `UpdateLive`. Read that line while the switch runs: the tile it reads is not special, which is the point — the position, cycle, pause flag and rate it reports are the whole switch's.

The same demo also has a headless mode that repeats the scenario over 1, 50, 200 and 1000 elements and writes a timing table; see [Verify & Complete Code](../../04_verify-and-complete-code/index.md).

**Expected result:** with 1000 elements the pause button freezes every tile at the same position, and the live readout keeps reporting that shared position.
