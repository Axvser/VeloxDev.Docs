# Data Flow — AOP, MonoBehaviour & WeakTypes

## 1. AOP property read (getter with start hook)

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_NS_Aop proxy" as P
participant "ProxyInstance" as PI
participant "Hook handlers" as H
participant "Real target (reflection)" as T

C -> P: Name { get; }    // call through Aop() proxy
activate P
P -> PI: Invoke(targetMethod = "get_Name", args)
activate PI
PI -> PI: GetterActions.TryGetValue("get_Name", out actions)
alt start != null
    PI -> H: start.Invoke(args, null)
    H --> PI: R0
end
alt coverage != null
    PI -> H: coverage.Invoke(args, R0)   // replaces original logic
    H --> PI: R1
else coverage == null   // error/fallback path: reflect into real target
    PI -> T: _targetType.GetMethod("get_Name").Invoke(_target, args)
    T --> PI: R1
end
alt end != null
    PI -> H: end.Invoke(args, R1)
    H --> PI: null
end
PI --> P: return R1
deactivate PI
P --> C: property value
deactivate P
@enduml
```

The same shape applies to `set_*` (writes to `SetterActions`) and plain methods (writes to `MethodActions`). A null `coverage` always falls back to `_targetType.GetMethod(Name)?.Invoke(_target, args)` (`ProxyInstance.cs` lines 23-53).

## 2. AOP method call with coverage overriding

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_NS_Aop proxy" as P
participant "ProxyInstance" as PI
participant "Coverage handler" as H
participant "Real target (reflection)" as T

C -> P: Reset()
activate P
P -> PI: Invoke(targetMethod = "Reset", args)
activate PI
PI -> PI: MethodActions.TryGetValue("Reset", out actions)
alt coverage != null
    PI -> H: coverage.Invoke(args, null)
    H --> PI: R1 = null
    Note over PI: original Reset() body is NOT executed
else coverage == null
    PI -> T: _targetType.GetMethod("Reset").Invoke(_target, args)
    T --> PI: R1
end
PI --> P: return R1
deactivate PI
P --> C: void
deactivate P
@enduml
```

Demo wiring: `p.SetProxy(ProxyMembers.Method, nameof(TeamViewModel.Reset), null, coverage, null)` cancels the default `Reset()` (`Examples/AOP/WPF/Demo/MainWindow.xaml.cs` lines 63-68).

## 3. MonoBehaviour frame loop

```plantuml
@startuml
!theme plain

participant "Client" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update thread" as U
participant "FixedUpdate thread" as F
participant "IMonoBehaviour" as B
participant "FrameEventArgs" as E

C -> M: Start(channel)
activate M
M -> L: GetOrCreateChannel(name).Start()
activate L
L -> L: spawn Update + FixedUpdate threads
L --> M: Started event
M --> C: OnChannelStarted
deactivate M

activate U
loop while IsRunning && !cts.Canceled
    U -> L: ProcessMainThreadOperations / config queue
    U -> L: CreateFrameEventArgs(deltaTime)
    L --> U: E (pooled)
    U -> B: InvokeUpdate(E)  ->  partial void Update(E)
    alt E.Handled == true
        U -> U: stop invoking further behaviors this frame
    end
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: FrameRateControlSync (sleep to 1/TargetFPS)
end
deactivate U

activate F
loop while IsRunning && !cts.Canceled
    F -> L: elapsed >= fixedUpdateInterval (16 ms)
    F -> L: CreateFrameEventArgs(elapsed)
    L --> F: E
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    F -> L: enqueue E for update-thread drain (if not Handled)
end
deactivate F

C -> M: StopAsync(channel)
activate M
M -> L: cts.Cancel(), join threads, clear queues, reset stats
L --> M: Stopped event
M --> C: OnChannelStopped
deactivate M
deactivate L
@enduml
```

Key loop source: `MonoBehaviourManager.cs` lines 394-441 (`FixedUpdateLoop`), 443-488 (`UpdateLoop`), 610-656 (`ExecuteBehaviorsUpdateSync` / `LateUpdate` / `FixedUpdate`), 245-291 (`Start`), 293-336 (`StopAsync`).

## 4. WeakDelegate — add + invoke

```plantuml
@startuml
!theme plain

participant "Publisher" as P
participant "WeakDelegate<T>" as W
participant "WeakReference<Delegate>" as WR
participant "Subscriber" as S

P -> W: AddHandler(handler)
activate W
W -> WR: new WeakReference<Delegate>(handler)
W -> W: _combinedDelegate = GetInvocationList()   // cached
deactivate W

note over WR,S: subscriber goes out of scope -> GC may collect target<br/>WeakDelegate keeps NO strong reference

P -> W: Invoke(object?[] args)
activate W
W -> W: lock; _combinedDelegate?.DynamicInvoke(args)
alt target still alive
    W -> S: handler executes
else target collected
    note over W: no-op; entry pruned on next GetInvocationList / Clone
end
deactivate W
@enduml
```

Source: `WeakDelegate.cs` lines 10-17 (`AddHandler`), 35-55 (`GetInvocationList`), 57-66 (`CleanupCollectedHandlers`), 68-74 (`Invoke`), 76-91 (`Clone`).
