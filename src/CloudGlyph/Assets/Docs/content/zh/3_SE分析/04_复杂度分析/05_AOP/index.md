# 复杂度分析 — AOP

AOP 的热点路径是代理缓存查找（`AopCache.Resolve`）、每次调用的分发（`ProxyInstance.Invoke`）以及 `coverage == null` 时的反射回退。下面的常量假设每个目标实例恰好一个 `Aop()` 代理——这正是每对类型 `ConditionalWeakTable` 所保证的。

## 代理解析（`AopCache.Resolve` / `Aop()`）

$$O(1) \text{ amortized per } Aop()$$

`AopCache.Resolve` 就是一次 `ConditionalWeakTable<TClass, TInterface>.GetValue` 调用（`AopCache.cs`，第 24-32 行；表声明于第 14-19 行）。`ConditionalWeakTable` 是带弱键的 CLR 哈希表，因此 get-or-create 查找是摊还 $O(1)$：

$$T_{\text{Aop()}} = O(1) \text{ amortized}$$

某个目标的首次调用要付一次工厂代价——`ProxyEx.CreateProxy` 运行 `DispatchProxy.Create<T, ProxyInstance>()`（`ProxyEx.cs`，第 17-25 行），分配实例并登记进静态 `ProxyIDs` 表。（`DispatchProxy` 只对整个 `(interface, ProxyInstance)` 对生成并缓存一次具体的代理*类型*，后续目标可跳过该步。）之后对该目标的每次 `Aop()` 都是纯缓存命中。由于每个目标实例只创建一个代理，单个实例的创建代价在其整个生命周期内摊还 $O(1)$。

## 分发 + 钩子查找（`ProxyInstance.Invoke`）

$$O(1) \text{ per dispatch} \;+\; O(h) \text{ hook handlers},\quad h \le 3$$

`Invoke` 只计算一次成员名（`ProxyInstance.cs`，第 25 行），按 `get_*` / `set_*` 前缀在三个字典中选一（第 29-52 行），再用 `Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>>` 解析钩子三元组（`GetterActions` / `SetterActions` / `MethodActions`，声明于第 19-21 行）。字典访问摊还 $O(1)$；分发本身不涉及反射。

随后每次被拦截调用要付出活动钩子的代价——至多三个处理器（`start`、`coverage`、`end`）：

$$T_{\text{intercept}} = O(1) + O(h),\quad h \le 3$$

## 反射回退路径（`coverage == null`）

当未注册 `coverage` 处理器（包括完全没有钩子的成员）时，`Invoke` 对真实目标做反射：

```csharp
// Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs（method 分支，第 49 行）
var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
```

`Type.GetMethod(string)` 对类型元数据做线性扫描，`MethodInfo.Invoke` 会对实参装箱：

$$O(m) \text{ lookup} + O(a) \text{ invoke},\quad m = \text{members in type},\; a = \text{argument count}$$

因此反射回退严格比 `coverage` 处理器更贵，也是无钩子成员的单次调用中占主导的代价。*该刻画由 `ProxyInstance.cs` 第 49 行的 `GetMethod` / `Invoke` 用法推出；底层算法属于标准 BCL 行为。*

## 逆向查找（`Aop.GetTarget`）

$$O(1) \text{ amortized}$$

`Aop.GetTarget<TTarget>` 是对 `ConditionalWeakTable<object, object>.TryGetValue` 的逆向查找（`Aop.cs`，第 13、25-26 行）——摊还 $O(1)$，与已映射的代理数量无关。

## 内存行为

| 结构 | 内存行为 |
|---|---|
| `AopCache.Entry<TClass,TInterface>.Instances` | 利用 CLR 泛型特化，每对 `(TClass, TInterface)` 一张 `ConditionalWeakTable<TClass, TInterface>`——弱键（目标）、强值（代理）。每个被代理目标一个缓存条目 |
| `Aop._proxyToTarget` | 一张 `ConditionalWeakTable<object, object>` 用于代理 → 目标逆向映射——弱键、强值 |
| `ProxyInstance.ProxyInstances` | `Dictionary<Guid, ProxyInstance>`——**静态强引用**注册表；每个被创建的 `ProxyInstance` 在构造函数中登记（第 13 行） |
| `ProxyInstance.ProxyIDs` | `Dictionary<object, Guid>`——**静态强引用**代理 → `Guid` 映射，由 `ProxyEx.CreateProxy` 填充（第 23 行） |
| 钩子字典 | 每个 `ProxyInstance` 三张 `Dictionary<string, Tuple<...>>`——$O(k)$ 条目，$k$ = 注册了钩子的不同成员数；空表各自为 $O(1)$ |

**滞留注意。** 两张静态注册表只增不减：条目在代理创建时加入，且没有任何移除/注销 API。由于 `ProxyInstance` 被 `ProxyInstances` / `ProxyIDs` 强引用，而它又持有对 `_target` 的强引用（`ProxyInstance.cs`，第 15 行），**一旦对该实例调用过 `Aop()`，代理与其目标都无法被回收**——即使应用已丢弃所有其它引用。每对类型的 `AopCache` 弱表与 `Aop._proxyToTarget` 在键上是弱的，但它们无法回收被静态注册表长期持有的代理。对长期运行、代理大量不同实例的程序而言，内存随被代理目标的去重数量线性增长。未挂钩子的成员不额外占内存，但每个实例仍会持有三张空钩子字典。

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| `Aop()` 代理解析（`AopCache.Resolve`） | 摊还 $O(1)$ |
| 代理创建（`DispatchProxy.Create`） | 每个 `(interface, ProxyInstance)` 对一次性类型生成；每个目标一次实例分配 + 登记 |
| `ProxyInstance.Invoke` 分发 | 摊还 $O(1)$（字典查找 + 前缀判断） |
| 钩子执行 | $O(h)$，$h \le 3$ |
| 被拦截调用合计 | $O(1) + O(h)$，$h \le 3$ |
| 反射回退（`coverage == null`） | $O(m) + O(a)$ |
| `Aop.GetTarget` 逆向查找 | 摊还 $O(1)$（CWT） |
| 内存（每对类型代理缓存） | 每个被代理目标 $O(1)$；键为弱引用，但静态注册表使代理与目标常驻 |
| 内存（静态注册表） | 强引用 `ProxyInstances` / `ProxyIDs`——随每个被代理目标增长，从不回收 |

> 出处汇总：`Src/Core/VeloxDev.Core/AspectOriented/{AopCache,Aop,ProxyInstance,ProxyEx}.cs`。
