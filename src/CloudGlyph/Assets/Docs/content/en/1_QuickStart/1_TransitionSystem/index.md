# Transition System — Quick Start

This guide gets you animating UI properties with the **Transition System** — VeloxDev's cross-platform, code-driven interpolation engine. The core idea is **"everything is a state"**: you record a target's property values into a *state snapshot*, describe where the object should end up, and execute it — the engine interpolates every recorded property from its current value to the target over a timed, eased, frame-based timeline.

> Demo source: `Examples/Transition/{WPF, Avalonia, WinUI, WinForms, MAUI, Blazor}/Demo`

## 1. Install / Add Dependency

Add the adapter package for your GUI framework — it brings the Transition engine plus platform interpolators:

```bash
# WPF
dotnet add package VeloxDev.WPF

# Avalonia
dotnet add package VeloxDev.Avalonia

# WinUI / MAUI / WinForms / Razor also available
```

## 2. Basic Setup / Registration

**Step 1 — create a state snapshot** with `Transition<T>.Create()` and record target property values. Property lambdas may be **nested paths** (e.g. `r => ((TranslateTransform)r.RenderTransform).X`):

```csharp
using VeloxDev.TransitionSystem;

// The fluent builder: record target values + an effect, then execute
private static readonly Transition<Rectangle>.StateSnapshot Animation0 =
    Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 0)
        .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            IsAutoReverse = true,
            LoopTime = 2,
        });
```

**Step 2 — platform wiring (only some platforms need it):**

- WPF / Avalonia: no wiring required — animations may even be started from a background thread; the adapter's `UIThreadInspector` marshals updates to the UI thread.
- WinUI: **required** — call `UIThreadInspector.SetWindow(this);` once, and do not create `Transition<T>` static fields on non-UI threads.
- WinForms / Razor: **required** — call `UIThreadInspector.CaptureUIThread();` on the UI thread (WinForms: in `OnLoad`; Razor: in `OnInitialized`).

## 3. Core Usage (Step by Step)

**Execute a snapshot** — by default one object runs only one animation at a time (`CanMutualTask: true`; a new animation cancels the running one). Pass `CanMutualTask: false` to allow parallel animations:

```csharp
Animation0.Execute(Rec0);                 // default: mutual-exclusive
Animation0.Execute(Rec0, CanMutualTask: false);

// Can be started from a non-UI thread
_ = Task.Run(() =>
{
    Animation0.Execute(Rec0);
    Animation1.Execute(Rec1);
    Animation2.Execute(Rec2);
});
```

**Chain multiple segments** with `.Await`, `.Then`, `.AwaitThen`, each with its own effect and easing:

```csharp
private static readonly Transition<Rectangle>.StateSnapshot Animation2 =
    Transition<Rectangle>.Create()
        .Property(r => r.RenderTransform,
        [
            new TranslateTransform(200, 0),
            new ScaleTransform(1.3, 1.3)
        ])
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            IsAutoReverse = true,
            FPS = 144,
            Ease = Eases.Circ.InOut,
            LoopTime = 2,
        })
        .AwaitThen(TimeSpan.FromSeconds(5)) // wait 5s before the next segment
        .Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            Ease = Eases.Sine.In
        });
```

**Capture a live snapshot** (record the object's *current* values for reset/undo):

```csharp
var snapshot0 = Rec0.SnapshotAll();                                    // every animatable property
var snapshot1 = Rec0.Snapshot(x => x.RenderTransform, x => x.Fill);    // specific properties
var snapshot2 = Rec0.SnapshotExcept(x => x.Visibility);                // all but these

// Reset the object back to the captured state instantly
btnReset.Click += (s, e) => snapshot1.Effect(TransitionEffects.Empty).Execute(Rec0);
```

**Stop animations**:

```csharp
// IncludeMutual    -> stops animations created with CanMutualTask: true
// IncludeNoMutual  -> stops animations created with CanMutualTask: false
Transition.Exit(Rec0, IncludeMutual: true, IncludeNoMutual: false);
Transition.Exit(Rec1);
```

## 4. Verification

Run the app:

- `Rec0` animates opacity, position and fill over 2 s, then auto-reverses twice (`IsAutoReverse + LoopTime: 2`).
- The multi-segment `Animation2` moves + scales, waits 5 s, then animates the fill color with a different easing.
- The Reset button restores `Rec1` to its captured state instantly.
- Interrupt buttons call `Transition.Exit(...)` and the rectangles freeze in place.
- All six platform demos (WPF, Avalonia, WinUI, WinForms, MAUI, Blazor) run the same animation definitions — the Blazor demo animates a plain `BoxModel` view-model and re-renders via `INotifyPropertyChanged`.

## 5. Complete Code

A minimal WPF window animating a rectangle:

```csharp
public partial class MainWindow : Window
{
    private static readonly Transition<Rectangle>.StateSnapshot Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
            .Effect(new TransitionEffect()
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
                Ease = Eases.Sine.InOut,
            });

    public MainWindow()
    {
        InitializeComponent();
        Loaded += (s, e) => Animation0.Execute(Rec0);
        btnExit.Click += (s, e) => Transition.Exit(Rec0);
    }
}
```

> **Note:** the Razor adapter adds a `string?` `Property` overload for animating CSS color strings (`"#ff7043"`, `rgb(...)`, named colors). WinForms animates `IInterpolable` + `Padding` + common numerics; MAUI animates MAUI types (`Brush`, `Shadow`, `PointF`, `RectF`, ...).
