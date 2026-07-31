# AOP、MonoBehaviour 与弱引用 — 快速入门

本页汇总 `VeloxDev.Core` 中三个横切性子系统：

- **AOP** — 基于生成的 `DispatchProxy` 的运行时面向切面拦截。仅支持新式 .NET：运行时所有源文件都包裹在 `#if NET` 中。
- **MonoBehaviour** — Unity 风格的帧循环（`Update` / `LateUpdate` / `FixedUpdate`），由专用后台线程驱动（WASM 上改用异步任务）。
- **弱引用（WeakTypes）** — 弱引用集合与事件包装，让 GC 可以回收订阅者 / 缓存目标。

三者都编译进同一个 `VeloxDev.Core` 包；C# 源生成器随包分发。

## AOP — 快速入门

### 1. 安装

添加 `VeloxDev.Core` NuGet 包。该包包含运行时（`VeloxDev.AspectOriented`），并依赖源生成器 `VeloxDev.Core.Generator`，后者在编译期生成代理接口和 `Aop()` 扩展方法。

> AOP 运行时只针对包的 `net5.0+` 目标编译（`#if NET`），在 `netstandard2.0` / `netframework4.6.1` 目标上不可用。

### 2. 用 `[AspectOriented]` 标记成员 + 定义 VM

在 `partial` 类上用 `[AspectOriented]` 标记字段 / 属性 / 方法。`[VeloxProperty]`（来自 `VeloxDev.MVVM`）把后备字段变成可观察属性，生成器会把两者都暴露为可拦截成员。

```csharp
using System.Collections.ObjectModel;
using System.Collections.Specialized;
using VeloxDev.AspectOriented;
using VeloxDev.MVVM;

namespace Demo;

public partial class TeamViewModel
{
    [VeloxProperty][AspectOriented] private string _name = string.Empty;
    [VeloxProperty][AspectOriented] private ObservableCollection<MemberViewModel> _members = [];

    [AspectOriented]
    public void Reset()
    {
        Name = string.Empty;
        Members.Clear();
    }

    [AspectOriented]
    public void AOP_OnMemberAdded(object? sender, NotifyCollectionChangedEventArgs e)
    {
        if (e.Action != NotifyCollectionChangedAction.Add) return;
    }
}
```

> 出处：`Examples/AOP/WPF/Demo/TeamViewModel.cs` 第 16-53 行（节选）。

生成器会生成接口 `VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop : IAspectOriented`（由 `AopInterface.cs` 生成，名称在第 30 行拼接）以及带缓存的 `Aop()` 扩展（由 `AopWriter.cs` 第 75-87 行生成）。每个目标只创建一次代理，缓存在 `ConditionalWeakTable` 中（`AopCache.Resolve`）。

### 3. 通过 `Aop().SetProxy(...)` 附加 start / coverage / end 钩子

```csharp
private static void ConfigureAOP(TeamViewModel data)
{
    var p = data.Aop();

    // start 钩子：在读取 Name [前]触发
    p.SetProxy(ProxyMembers.Getter,
        nameof(TeamViewModel.Name),
        (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
        null,
        null);

    // end 钩子：在写入 Name [后]触发
    p.SetProxy(ProxyMembers.Setter,
        nameof(TeamViewModel.Name),
        null,
        null,
        (p, _) => { MessageBox.Show($"the name of team has been changed to {p?[0]}"); return null; });

    // coverage 钩子：覆写原来的 Reset() 逻辑
    p.SetProxy(ProxyMembers.Method,
        nameof(TeamViewModel.Reset),
        null,
        (_, _) => { MessageBox.Show($"the default Reset() has been cancelled"); return null; },
        null);
}
```

> 出处：`Examples/AOP/WPF/Demo/MainWindow.xaml.cs` 第 45-95 行（节选）。

`SetProxy(ProxyMembers.Getter|Setter|Method, memberName, start, coverage, end)` 注册一个 `(ProxyHandler?, ProxyHandler?, ProxyHandler?)` 三元组（见 `ProxyEx.cs` 第 26-41 行）。每个处理器形如 `object? ProxyHandler(object?[]? parameters, object? previous)`。`coverage` 非空时替换原逻辑；为 `null` 时，`ProxyInstance.Invoke` 回退为对真实目标做反射调用（见 `ProxyInstance.cs` 第 23-53 行）。

### 4. 验证

通过代理调用成员并观察钩子顺序：

```csharp
var team = _teamData.Aop();
_ = team.Name;                       // getter start 钩子 -> MessageBox
team.Name = "New Team Name";         // setter end 钩子   -> MessageBox
team.Reset();                        // coverage 钩子     -> 默认逻辑被取消
team.Members.Add(new MemberViewModel() { Name = "Jack" });  // AOP_OnMemberAdded end 钩子
```

> 出处：`Examples/AOP/WPF/Demo/MainWindow.xaml.cs` 第 18-42 行（`Click0`..`Click4`）。

## MonoBehaviour — 快速入门

### 1. 安装

同一个包：添加 `VeloxDev.Core`。`VeloxDev.Core.Generator` 源生成器把 `[MonoBehaviour]` 类变成 `VeloxDev.MonoBehaviour.IMonoBehaviour` 实现。

### 2. 标记类 `[MonoBehaviour]` + partial Update / FixedUpdate

```csharp
using VeloxDev.TimeLine;

namespace Demo;

[MonoBehaviour]
public partial class MainWindow : Window
{
    [MonoBehaviour]
    private partial class PhysicsComponent
    {
        private int _updateCount = 0;
        private double _velocity = 0;
        private const double Gravity = 9.8;

        public PhysicsComponent() => InitializeMonoBehaviour();

        partial void Update(FrameEventArgs e)
        {
            _updateCount++;
            _velocity += Gravity * e.DeltaTime.TotalSeconds;
        }

        partial void FixedUpdate(FrameEventArgs e)
        {
            _fixedUpdateCount++;
        }
    }
}
```

> 出处：`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs` 第 8-33 行（节选）。

生成器生成 `InitializeMonoBehaviour()` / `CloseMonoBehaviour()`（注册 / 注销）并声明 partial 钩子 `Awake`、`Start`、`Update(FrameEventArgs)`、`LateUpdate(FrameEventArgs)`、`FixedUpdate(FrameEventArgs)`（见 `Writers/MonoWriter.cs` 第 80-120 行）。调用 `InitializeMonoBehaviour()` 即完成注册；管理器在注册时调用 `InvokeAwake` / `InvokeStart`，之后每帧调用各回调。

### 3. 启动循环

```csharp
public MainWindow()
{
    InitializeComponent();
    Loaded += (s, e) =>
    {
        _physics = new PhysicsComponent();   // 构造函数里调用了 InitializeMonoBehaviour()
        InitializeMonoBehaviour();           // 也注册本窗口
        MonoBehaviourManager.Start();        // 启动 "default" 通道
    };

    Closing += async (s, e) =>
    {
        await MonoBehaviourManager.StopAsync();
    };
}
```

> 出处：`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs` 第 95-115 行（节选）。

### 4. 配置

通过静态管理器做配置（按通道；所有方法都带可选 `channel` 参数，默认为 `"default"`）：

```csharp
MonoBehaviourManager.SetTargetFPS(30, "game");       // 钳位：1..1000
MonoBehaviourManager.SetTimeScale(0.5f);             // 钳位：0..10
MonoBehaviourManager.SetFixedUpdateInterval(16);     // 毫秒，钳位：1..1000
```

> 出处：`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourManager.cs` 第 184-210 行（按通道的设置器）；demo 第 50 行在 `Update` 里调用 `MonoBehaviourManager.SetTargetFPS(30,"game")`。

### 5. 停止

```csharp
await MonoBehaviourManager.StopAsync();   // 取消两个线程、重置统计、触发 Stopped
```

### 6. 验证

从循环内或 UI 线程查询实时状态：

```csharp
MonoBehaviourManager.IsRunning();
MonoBehaviourManager.CurrentFPS();
MonoBehaviourManager.ActiveBehaviorCount();
MonoBehaviourManager.IsUpdateThreadAlive();
MonoBehaviourManager.IsFixedUpdateThreadAlive();
```

> 出处：`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs` 第 182-188 行；查询 API 见 `MonoBehaviourManager.cs` 第 1070-1105 行。

## 弱引用（WeakTypes）— 快速入门

> WeakTypes 没有配套 demo 工程；以下用法**根据运行时源码与 MSTest 测试推导**，标注为*推断（inferred）*。

### 1. 安装

同一个 `VeloxDev.Core` 包；命名空间 `VeloxDev.WeakTypes`。四个类型在包的所有目标框架上都可用。

### 2. 用 `WeakDelegate` 实现无泄漏事件

*推断用法。* `WeakDelegate<TDelegate>` 存储 `WeakReference<Delegate>` 而非强引用，事件发布者不会持有订阅者的强引用：

```csharp
using VeloxDev.WeakTypes;

var changed = new WeakDelegate<Action<string>>();
changed.AddHandler(name => Console.WriteLine($"name = {name}"));

// 订阅者存活期间处理器一直生效
changed.Invoke(["VeloxDev"]);

// 组合委托会被缓存；Clone() 从存活处理器重建
var snapshot = changed.Clone();
```

> 出处：`Src/Core/VeloxDev.Core/WeakTypes/WeakDelegate.cs` 第 10-91 行；调用形如 `Invoke(object?[] objects)`（第 68 行），由 `WeakDelegateTests.cs` 第 9-19 行（`wd.Invoke([42])`）验证。

### 3. `WeakQueue` / `WeakStack`

*推断用法。* 元素弱持有；`TryDequeue` / `TryPop` / `TryPeek` 会跳过目标已被回收的条目：

```csharp
var queue = new WeakQueue<string>();
queue.Enqueue("a");
queue.EnqueueRange(["b", "c"]);
if (queue.TryPeek(out var front)) { }      // "a"，不删除
if (queue.TryDequeue(out var item)) { }    // "a"
queue.TrimExcess();

var stack = new WeakStack<string>();
stack.Push("a");
if (stack.TryPop(out var top)) { }         // "a"
```

> 出处：`WeakQueue.cs` 第 34-120 行、`WeakStack.cs` 第 34-122 行；顺序由 `WeakQueueTests.cs` 第 26-39 行（FIFO）和 `WeakStackTests.cs` 第 26-39 行（LIFO）验证。

### 4. `WeakCache`

*推断用法。* `WeakCache<TTargetKey, TCacheKey>` 通过 `ConditionalWeakTable` 把弱键映射到缓存值，并周期性清扫已回收目标：

```csharp
var cache = new WeakCache<ViewModel, Visual>();
cache.AddOrUpdate(vm, visual);

if (cache.TryGetCache(vm, out var v)) { }   // 摊还 O(1)
cache.ForeachCache((key, val) => Release(val));
cache.Remove(vm);
```

> 出处：`WeakCache.cs` 第 14-79 行；行为由 `WeakCacheTests.cs` 第 9-87 行验证。
