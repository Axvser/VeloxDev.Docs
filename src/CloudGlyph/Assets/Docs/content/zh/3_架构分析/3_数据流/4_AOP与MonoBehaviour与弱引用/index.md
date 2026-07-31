# 数据流 — AOP、MonoBehaviour 与弱引用

## 1. AOP 属性读取（getter + start 钩子）

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_NS_Aop 代理" as P
participant "ProxyInstance" as PI
participant "钩子处理器" as H
participant "真实目标（反射）" as T

C -> P: Name { get; }    // 通过 Aop() 代理调用
activate P
P -> PI: Invoke(targetMethod = "get_Name", args)
activate PI
PI -> PI: GetterActions.TryGetValue("get_Name", out actions)
alt start != null
    PI -> H: start.Invoke(args, null)
    H --> PI: R0
end
alt coverage != null
    PI -> H: coverage.Invoke(args, R0)   // 替换原逻辑
    H --> PI: R1
else coverage == null   // 回退路径：反射进入真实目标
    PI -> T: _targetType.GetMethod("get_Name").Invoke(_target, args)
    T --> PI: R1
end
alt end != null
    PI -> H: end.Invoke(args, R1)
    H --> PI: null
end
PI --> P: 返回 R1
deactivate PI
P --> C: 属性值
deactivate P
@enduml
```

`set_*`（写入 `SetterActions`）与普通方法（写入 `MethodActions`）形状相同。`coverage` 为 `null` 时总是回退到 `_targetType.GetMethod(Name)?.Invoke(_target, args)`（`ProxyInstance.cs` 第 23-53 行）。

## 2. AOP 方法调用（coverage 覆写）

```plantuml
@startuml
!theme plain

actor Caller as C
participant "X_NS_Aop 代理" as P
participant "ProxyInstance" as PI
participant "coverage 处理器" as H
participant "真实目标（反射）" as T

C -> P: Reset()
activate P
P -> PI: Invoke(targetMethod = "Reset", args)
activate PI
PI -> PI: MethodActions.TryGetValue("Reset", out actions)
alt coverage != null
    PI -> H: coverage.Invoke(args, null)
    H --> PI: R1 = null
    Note over PI: 原始 Reset() 方法体不执行
else coverage == null
    PI -> T: _targetType.GetMethod("Reset").Invoke(_target, args)
    T --> PI: R1
end
PI --> P: 返回 R1
deactivate PI
P --> C: void
deactivate P
@enduml
```

demo 接线：`p.SetProxy(ProxyMembers.Method, nameof(TeamViewModel.Reset), null, coverage, null)` 取消默认的 `Reset()`（`Examples/AOP/WPF/Demo/MainWindow.xaml.cs` 第 63-68 行）。

## 3. MonoBehaviour 帧循环

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "MonoBehaviourManager" as M
participant "LoopChannel" as L
participant "Update 线程" as U
participant "FixedUpdate 线程" as F
participant "IMonoBehaviour" as B
participant "FrameEventArgs" as E

C -> M: Start(channel)
activate M
M -> L: GetOrCreateChannel(name).Start()
activate L
L -> L: 创建 Update + FixedUpdate 线程
L --> M: Started 事件
M --> C: OnChannelStarted
deactivate M

activate U
loop 当 IsRunning && !cts.Canceled
    U -> L: ProcessMainThreadOperations / 配置队列
    U -> L: CreateFrameEventArgs(deltaTime)
    L --> U: E（对象池）
    U -> B: InvokeUpdate(E)  ->  partial void Update(E)
    alt E.Handled == true
        U -> U: 本帧不再调用后续行为
    end
    U -> B: InvokeLateUpdate(E) -> partial void LateUpdate(E)
    U -> L: FrameRateControlSync（睡眠到 1/TargetFPS）
end
deactivate U

activate F
loop 当 IsRunning && !cts.Canceled
    F -> L: elapsed >= fixedUpdateInterval（16 ms）
    F -> L: CreateFrameEventArgs(elapsed)
    L --> F: E
    F -> B: InvokeFixedUpdate(E) -> partial void FixedUpdate(E)
    F -> L: 未 Handled 时入队 E 供 Update 线程排空
end
deactivate F

C -> M: StopAsync(channel)
activate M
M -> L: cts.Cancel()、汇合线程、清空队列、重置统计
L --> M: Stopped 事件
M --> C: OnChannelStopped
deactivate M
deactivate L
@enduml
```

关键循环源码：`MonoBehaviourManager.cs` 第 394-441 行（`FixedUpdateLoop`）、443-488 行（`UpdateLoop`）、610-656 行（`ExecuteBehaviorsUpdateSync` / `LateUpdate` / `FixedUpdate`）、245-291 行（`Start`）、293-336 行（`StopAsync`）。

## 4. WeakDelegate — 添加 + 调用

```plantuml
@startuml
!theme plain

participant "发布者" as P
participant "WeakDelegate<T>" as W
participant "WeakReference<Delegate>" as WR
participant "订阅者" as S

P -> W: AddHandler(handler)
activate W
W -> WR: new WeakReference<Delegate>(handler)
W -> W: _combinedDelegate = GetInvocationList()   // 缓存
deactivate W

note over WR,S: 订阅者离开作用域 -> GC 可能回收目标<br/>WeakDelegate 不保留任何强引用

P -> W: Invoke(object?[] args)
activate W
W -> W: lock; _combinedDelegate?.DynamicInvoke(args)
alt 目标仍存活
    W -> S: 处理器执行
else 目标已回收
    note over W: 无操作；下次 GetInvocationList / Clone 时剪除
end
deactivate W
@enduml
```

出处：`WeakDelegate.cs` 第 10-17 行（`AddHandler`）、35-55 行（`GetInvocationList`）、57-66 行（`CleanupCollectedHandlers`）、68-74 行（`Invoke`）、76-91 行（`Clone`）。
