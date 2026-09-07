# MonoBehaviour — Pause, Resume & Restart

Lifecycle control beyond `Start` / `StopAsync` (covered on the [Configure & Run the Loop](../03_configure-and-run-the-loop/) page) is three methods plus a toggle, all per channel.

## 1. Pause

`Pause` does not stop the pumps; it sets the channel's paused flag and both pumps go into a low-cost idle loop (roughly a 10 ms sleep) in which no `Update`, `LateUpdate` or `FixedUpdate` is dispatched and the statistics do not advance:

```csharp
MonoBehaviourManager.Pause("game");
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));   // "Paused"
Console.WriteLine(MonoBehaviourManager.IsPaused("game"));       // True
```

**Expected result:** while paused, behaviour counters stop growing and `TotalFrames` / `TotalTime` freeze.

## 2. Resume

`Resume` clears the paused flag and the pumps continue from where they left off:

```csharp
MonoBehaviourManager.Resume("game");
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));   // "Running"
```

**Expected result:** after `Resume`, the status returns to `"Running"` and frame dispatch resumes.

## 3. TogglePause

`TogglePause` flips the current state: if the channel is paused it resumes, otherwise it pauses.

```csharp
MonoBehaviourManager.TogglePause("game");
```

**Expected result:** repeated calls alternate `SystemStatus` between `"Paused"` and `"Running"`.

## 4. Restart

`RestartAsync` performs a clean stop followed by a fresh start on the same channel: it cancels and joins the pumps (1 s shutdown timeout, with a force cleanup if that is exceeded), waits for the pending add/remove/config queues to drain (500 ms budget), then calls `Start` again. On the way it raises `OnChannelStopped` and then `OnChannelStarted`:

```csharp
await MonoBehaviourManager.RestartAsync("game");
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));   // "Running"
```

**Expected result:** after `RestartAsync` the channel is `"Running"` again, its statistics are reset (`TotalFrames` restarts near zero), and registered behaviours remain active — but their `Awake` / `Start` hooks are not invoked a second time, because the loop only calls those when a behaviour is first picked up from the add-queue.

## 5. Pause / resume in one observable window

The complete program on the [Verify & Complete Code](../06_verify-and-complete-code/) page samples the counter twice while paused to prove nothing advances:

```csharp
MonoBehaviourManager.Pause("game");
long a = Volatile.Read(ref counter.UpdateCount);
await Task.Delay(300);
long b = Volatile.Read(ref counter.UpdateCount);
Console.WriteLine($"Updates grew while paused: {b - a}");   // 0

MonoBehaviourManager.Resume("game");
```

**Expected result:** the printed growth is `0` while paused, and positive again once resumed.

## Run declaration

- ⚠️ Statically verified only — the paused/window, resume and restart behavior above is transcribed from the loop bodies in `MonoBehaviourManager.cs`; it is exercised end-to-end by the recorded run on the [Verify & Complete Code](../06_verify-and-complete-code/) page.
