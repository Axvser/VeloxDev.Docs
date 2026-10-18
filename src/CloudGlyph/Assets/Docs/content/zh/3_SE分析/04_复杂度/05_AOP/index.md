# 复杂度 — AOP

热点路径是 `Aop()` 中的缓存查找、生成代理里的逐调用分支，以及钩子管线。由于代理是生成的 C#，没有反射阶段需要计价：旧设计的 `Type.GetMethod` + `MethodInfo.Invoke` 成本已完全消失。

## 代理解析 —— `AopCache.Resolve`

$$
T_{\text{Aop()}} = O(1) \text{ amortized}
$$

`AopCache.Resolve` 是一次 `ConditionalWeakTable<TClass, TInterface>.GetValue` 调用（`AopCache.cs`）。`ConditionalWeakTable` 是带弱键的 CLR 哈希表，命中与未命中的查找都是摊还 $O(1)$。对某目标的首次调用支付一次工厂成本：

$$
T_{\text{first}} = O(1) \text{ construction} + O(1) \text{ CWT insert} + O(1) \text{ reverse-map insert}
$$

`new {Interface}Proxy(target)` 分配一个对象：一个 `_target` 字段，加上每个可拦截访问器一个 `AspectHooks?` 字段。运行期没有类型生成，因此不像 `DispatchProxy` 那样存在按接口的一次性 `Reflection.Emit` 成本。

## 钩子安装 —— `ProxyEx.SetProxy`

$$
T_{\text{SetProxy}} = O(1)
$$

方法执行两次类型/身份检查、构造一个短字符串（`get_` / `set_` 前缀或无前缀）、分配一个 `AspectHooks`，并执行一个 `switch` 分支。重复安装直接覆盖字段；没有列表遍历，也没有字典。

## 被拦截的调用

### 无钩子（常见情形）

$$
T_{\text{call}} = O(1) + O(a)
$$

其中 $a$ 是调用自身的实参求值成本。生成的快速路径是：

```csharp
var h = _hooks_Add;
if (h is null)
{
    return _target.Add(a, b);
}
```

没有数组、没有装箱、没有委托调用、没有查找。每个从未注册的成员都走这条路径。

### 有钩子

$$
T_{\text{hooked}} = O(1) + O(a) + O(h), \quad h \le 3
$$

- 读取一次 `_hooks_*` 字段。
- 实参装箱进 `object?[]` —— 带参数的方法与 setter 分配一个数组；getter 与无参数方法传 `null`，不分配。
- 最多三次委托调用（`Start`、`Coverage`、`End`）。
- 值类型成员在返回路径上做一次拆箱转换。

`Coverage == null` 不增加阶段；它用方法体替代委托调用。即使方法体是 `void`，`End` 也会被调用（此时 `r1 == null`）。

### 与已移除的反射路径对照

旧设计的回退路径是：

$$
O(m) \text{ metadata scan} + O(a) \text{ boxing} + O(a) \text{ argument array}
$$

即 `Type.GetMethod(name)` 与 `MethodInfo.Invoke`，且**每次调用**都要支付。生成路径把 $O(m)$ 扫描换成直接调用，同时移除了目标异常上的 `TargetInvocationException` 包装。

## 代理到目标的查找 —— `Aop.GetTarget`

$$
O(1) \text{ amortized}
$$

一次 `ConditionalWeakTable<object, object>.TryGetValue`。与已映射代理的数量无关。

## 内存

| 结构 | 行为 |
|---|---|
| `AopCache.Entry<TClass,TInterface>.Instances` | 通过泛型特化为每一对 `(TClass, TInterface)` 提供一个 `ConditionalWeakTable`。弱键 = 目标，强值 = 代理。每个存活的可代理目标一个条目。 |
| 代理实例 | $O(m)$，$m$ = 可拦截访问器数量：`_target` 加每个访问器一个 `AspectHooks?` 字段。未挂钩的成员保持 `null`。 |
| `AspectHooks` | 每组三个委托引用；被替换，不会累积。 |
| `Aop._proxyToTarget` | 一个 `ConditionalWeakTable<object, object>`：弱键 = 代理，强值 = 目标。 |

**保持性。** 这里**没有静态强注册表**。`AopCache` 只在目标可达时保持代理存活，而 `Aop` 以代理为键。目标一旦不可达，代理与反向条目会一起被回收 —— `ConditionalWeakTable` 的 ephemeron 语义处理了 目标 → 代理 → 目标 的环。`AProxyIsCollectableOnceItsTargetIs` 断言了这一点：

```csharp
Assert.IsFalse(target.IsAlive, "nothing outside the proxy may root the target");
Assert.IsFalse(proxy.IsAlive, "and no static registry may root the proxy");
```

因此内存随**存活**的可代理目标数量增长，而不是随曾经创建过的数量增长。

**裁剪。** 生成的代理不含反射；`AopCache` 对 `TInterface` 的 `DynamicallyAccessedMembers` 标注只为满足裁剪器对 `ConditionalWeakTable` 的要求；`GetOrCreateValue` 从未被调用。

## 逐操作汇总

| 操作 | 时间 | 分配 |
|---|---|---|
| `Aop()` —— 命中缓存 | $O(1)$ 摊还 | 无 |
| `Aop()` —— 首次调用 | $O(1)$ | 一个代理、一个 CWT 条目、一个弱映射条目 |
| `SetProxy` | $O(1)$ | 一个 `AspectHooks` |
| 无钩子成员调用 | $O(1) + O(a)$ | 除调用本身外无 |
| 有钩子 getter | $O(1) + O(h)$ | 实参无分配 |
| 有钩子 setter / 带参方法 | $O(1) + O(a) + O(h)$ | 一个 `object?[]` |
| `Aop.GetTarget` | $O(1)$ 摊还 | 无 |

> 源码：`Src/Core/VeloxDev.Core/AspectOriented/{AopCache,Aop,ProxyEx,AspectHooks}.cs`、`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`、`Src/Core/VeloxDev.Core.Test/AspectOriented/AopProxyTests.cs`。
