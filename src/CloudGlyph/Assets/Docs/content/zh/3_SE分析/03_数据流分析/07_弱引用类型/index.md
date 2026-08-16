# 数据流 — 弱引用类型

四个类型都以锁保护；死亡引用在访问时被跳过或剪除。下面的时序图追踪三种代表性流程。

## 1. WeakQueue — 入队、回收、出队跳过死亡引用

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "WeakQueue~T~" as W
participant "WeakReference~T~" as WR
participant "GC" as G

C -> W: Enqueue(new Payload(1))
activate W
W -> WR: new WeakReference~T~(item)
W --> C: void
deactivate W

note over WR,G: 该 Payload 没有其他强引用 -> GC 回收它

C -> G: GC.Collect()
G -> WR: 目标被清空（TryGetTarget -> false）

C -> W: TryDequeue(out item)
activate W
W -> WR: Dequeue() 后 TryGetTarget(out item)
WR --> W: false（已死）
W -> W: 循环继续处理下一引用
note over W: 死亡条目被丢弃，不返回
W --> C: false / 下一个存活条目
deactivate W
@enduml
```

运行时探针，2026-08-17：`GC.Collect()` 之后队列报告 `Count: 1`，`TryDequeue` 只返回仍存活的那个条目。

## 2. WeakCache — AddOrUpdate 与周期清扫

```plantuml
@startuml
!theme plain

participant "客户端" as C
participant "WeakCache~K~V~" as W
participant "ConditionalWeakTable" as T
participant "清扫 List~WeakReference~K~~" as L

C -> W: AddOrUpdate(key, value)
activate W
W -> W: _counter++ ; 若 _counter > _perceptionThreshold
alt 越过阈值
    W -> L: RemoveAll(w => !w.TryGetTarget(out _))
    W -> W: _counter = 0
    W -> W: _perceptionThreshold = GetNextCleanupThreshold(count)
end
W -> T: Add(key, value)（替换已有）
W -> L: Add(new WeakReference~K~(key))
W --> C: void
deactivate W

note over T: 键在别处被回收 -> ConditionalWeakTable 条目自动消失

C -> W: TryGetCache(key, out value)
activate W
W -> T: TryGetValue(key)
alt 键存活
    T --> W: value
    W --> C: true
else 键已回收
    T --> W: miss
    W --> C: false
end
deactivate W
@enduml
```

出处：`WeakCache.cs` 第 44-63 行（`AddOrUpdate`）、31-43 行（`TryGetCache`）、75-79 行（`GetNextCleanupThreshold`）。

## 3. WeakDelegate — 调用 / 克隆时剪除已回收处理器

```plantuml
@startuml
!theme plain

participant "发布者" as P
participant "WeakDelegate~T~" as W
participant "WeakReference~Delegate~" as WR
participant "订阅者" as S

P -> W: AddHandler(live.Handle)
P -> W: AddHandler(dead.Handle, CanUpdateCache: false)
note over W: 缓存保持 null（或仅含 live）；dead 只被弱持有

note over WR,S: dead 订阅者离开作用域 -> GC 回收它

P -> W: Invoke([args])
activate W
alt 缓存为 null
    W -> W: RebuildCache()
    W -> WR: 逐个 TryGetTarget
    WR --> W: live -> 组合；dead -> 跳过
    W -> W: _combinedDelegate = 组合后的存活处理器
end
W -> S: 执行 live 处理器（dead 已被剪除）
W --> P: void
deactivate W

P -> W: Clone()
activate W
W -> W: 仅从存活处理器重建
W --> P: 新的 WeakDelegate（无 dead 处理器）
deactivate W
@enduml
```

出处：`WeakDelegate.cs` 第 10-19 行（`AddHandler`）、40-51 行（`GetInvocationList`）、62-76 行（`RebuildCache`）、78-87 行（`CleanupCollectedHandlers`）、89-104 行（`Clone`）。运行时探针，2026-08-17：GC 之后调用原实例只运行存活处理器（计数器 `1`），调用 `Clone` 也只运行存活处理器（计数器 `2`）。
