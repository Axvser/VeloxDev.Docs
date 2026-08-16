# 复杂度分析 — AOP

## 代理缓存查找（`AopCache.Resolve`）

$$O(1) \text{ 摊还，每次 } \text{Aop()}$$

`AopCache.Resolve` 就是一次 `ConditionalWeakTable<TClass, TInterface>.GetValue` 调用（`AopCache.cs` 第 24-32 行）。`ConditionalWeakTable` 是带弱键的 CLR 哈希表，因此 get-or-create 查找是摊还 $O(1)$，且代理**每个目标实例只创建一次**——之后每次 `Aop()` 都是缓存命中。

$$T_{\text{Aop()}} = O(1) \text{ 摊还}$$

## 分发 + 钩子查找（`ProxyInstance.Invoke`）

$$O(1) \text{ 每次分发, } + O(h) \text{ 个钩子处理器}, \quad h \le 3$$

`Invoke` 把成员名归一化一次，然后用 `Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>>` 解析钩子三元组（`GetterActions` / `SetterActions` / `MethodActions` —— `ProxyInstance.cs` 第 19-21、29-31 行）。字典访问摊还 $O(1)$；成员名已由 `DispatchProxy` 分发归一化（`get_*` / `set_*` 前缀）。

随后每次被拦截调用要付出活动钩子的代价——至多三个处理器（start、coverage、end）：

$$T_{\text{intercept}} = O(1) + O(h), \quad h \le 3$$

## 反射回退路径（`coverage == null`）

当 `coverage == null` 时，`Invoke` 对真实目标做反射：

```csharp
_targetType?.GetMethod(Name)?.Invoke(_target, args)
```

`Type.GetMethod(string)` 对类型元数据做线性扫描，`MethodInfo.Invoke` 会对参数装箱：

$$O(m) \text{ 查找 } + O(a) \text{ 调用}, \quad m = \text{类型中的成员数}, \ a = \text{实参个数}$$

因此反射回退严格比 `coverage` 处理器更贵。*该代价刻画由 `ProxyInstance.cs` 第 33 行的 `GetMethod` / `Invoke` 用法推断；底层算法属于标准 BCL 行为。*

## 逆向查找（`Aop.GetTarget`）

$$O(1) \text{ 摊还}$$

`Aop.GetTarget<TTarget>` 是对 `ConditionalWeakTable<object, object>.TryGetValue` 的逆向查找（`Aop.cs` 第 19-26 行）——摊还 $O(1)$，与已映射的代理数量无关。

## 内存行为（弱表）

| 结构 | 内存行为 |
|---|---|
| `AopCache.Entry<TClass,TInterface>` | 利用 CLR 泛型特化，每对 `(TClass, TInterface)` 一张 `ConditionalWeakTable`——**弱键**，代理随目标一起被回收；不生成每个类的缓存代码 |
| `Aop._proxyToTarget` | 一张 `ConditionalWeakTable<object, object>` 用于代理 → 目标逆向映射——弱键，不会让代理常驻 |
| `ProxyInstance.ProxyInstances` | `Dictionary<Guid, ProxyInstance>`——**强**引用静态注册表；条目只在 `ProxyInstance` 构造函数生命周期内登记，因此已登记于此的代理在注销前不会被回收 |
| `ProxyInstance.ProxyIDs` | `Dictionary<object, Guid>`——从代理到 `Guid` 的**强**引用；与 `ProxyInstances` 配合供 `SetProxy` 解析 |
| 钩子表 | 每个 `ProxyInstance` 有 $O(k)$ 条 `Dictionary` 条目，$k$ = 已注册钩子的不同成员数 |

> 注意：静态的 `ProxyInstances` / `ProxyIDs` 字典是强引用，会随每个已登记且未释放的代理一起增长。对于创建大量目标的长期运行程序，登记在这些表中的未释放代理无法被回收。而每对类型的 `AopCache` 表与 `Aop._proxyToTarget` 是弱表，不构成滞留隐患。

## 单操作汇总

| 操作 | 复杂度 |
|---|---|
| `Aop()` 代理解析（`AopCache.Resolve`） | 摊还 $O(1)$ |
| `ProxyInstance.Invoke` 分发 | 摊还 $O(1)$（字典查找） |
| 钩子执行 | $O(h)$，$h \le 3$ |
| 被拦截调用合计 | $O(1) + O(h)$，$h \le 3$ |
| 反射回退（`coverage == null`） | $O(m) + O(a)$ |
| `Aop.GetTarget` 逆向查找 | 摊还 $O(1)$（CWT） |
| 内存（代理缓存） | 每对类型弱表——代理随目标回收 |
| 内存（静态注册表） | 强引用 `ProxyInstances` / `ProxyIDs`——随已登记代理增长 |

> 出处汇总：`Src/Core/VeloxDev.Core/AspectOriented/{AopCache,Aop,ProxyInstance}.cs`。
