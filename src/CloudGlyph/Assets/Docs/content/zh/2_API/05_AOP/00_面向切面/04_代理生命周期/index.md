# AOP 运行时 — `Aop` 与 `AopCache`

生成的 `Aop()` 入口背后的生命周期辅助。`Aop` 维护代理 → 目标的逆向映射（用于把代理还原为原始实例）；`AopCache` 为每个目标实例缓存一个代理，使 `Aop()` 返回稳定代理。

## 类型：`Aop`（静态类）

`Src/Core/VeloxDev.Core/AspectOriented/Aop.cs`：

```csharp
public static class Aop
{
    private static readonly ConditionalWeakTable<object, object> _proxyToTarget = [];

    public static void Map(object proxy, object target)
        => _proxyToTarget.Add(proxy, target);

    public static TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class
        => _proxyToTarget.TryGetValue(proxy, out var t) ? (TTarget)t : null;
}
```

### Aop.Map

**签名：** `void Map(object proxy, object target)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `proxy` | `object` | AOP 代理 |
| `target` | `object` | 代理包裹的原始实例 |

**返回：** `void`

**异常：** 未声明（重复键会抛 `ArgumentException`，但 `Aop()` 经由 `AopCache` 保证每个代理只注册一次）。

**备注：** 向静态 `ConditionalWeakTable<object, object>` 添加 `proxy → target`。由生成的 `Aop()` 扩展在 `ProxyEx.CreateProxy` 之后立即调用。弱表意味着代理只在目标存活期间被保持。

### Aop.GetTarget\<TTarget\>

**签名：** `TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class`

| 参数 | 类型 | 说明 |
|---|---|---|
| `proxy` | `IAspectOriented` | 要做逆向映射的 AOP 代理 |

**返回：** `TTarget?` — 原始目标实例；若该代理从未被映射则返回 `null`。

**异常：** 无。

**备注：** 在同一张 `ConditionalWeakTable` 上做逆向查找 —— 摊还 `O(1)`。其签名由运行时源码推断而来（无 Demo / 测试使用它）；自然用法如 `var original = Aop.GetTarget<TeamViewModel>(team);`。

## 类型：`AopCache`（静态类）

`Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs`：

```csharp
public static class AopCache
{
    private static class Entry<TClass, TInterface>
        where TClass : class
        where TInterface : class, IAspectOriented
    {
        public static readonly ConditionalWeakTable<TClass, TInterface> Instances = [];
    }

    public static TInterface Resolve<TClass, TInterface>(
        TClass instance,
        Func<TClass, TInterface> factory)
        where TInterface : class, IAspectOriented
        where TClass : class
    {
        return Entry<TClass, TInterface>.Instances
            .GetValue(instance, k => factory(k));
    }
}
```

### AopCache.Resolve\<TClass, TInterface\>

**签名：** `TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory) where TInterface : class, IAspectOriented where TClass : class`

| 参数 | 类型 | 说明 |
|---|---|---|
| `instance` | `TClass` | 作为缓存键的目标实例 |
| `factory` | `Func<TClass, TInterface>` | 当 `instance` 还没有缓存代理时，用于创建代理 |

**返回：** `TInterface` — 若已缓存则返回缓存代理，否则返回 `factory` 的结果并将其存入缓存。

**异常：** 未声明。

**备注：**

- 通过嵌套泛型 `Entry<TClass, TInterface>`（CLR 泛型特化），为每一对 `(TClass, TInterface)` 提供独立的 `ConditionalWeakTable<TClass, TInterface>` —— 无需按类生成缓存代码。
- 采用 `ConditionalWeakTable.GetValue` 语义：工厂每个实例最多执行一次；条目随实例存活（弱键），因此代理与其目标一起被 GC 回收。
- 这正是 `_teamData.Aop()` 反复调用仍返回同一代理的原因（`Examples/AOP/WPF/Demo/MainWindow.xaml.cs`）。

相关页面：[ProxyEx](../02_proxyex/index.md) 提供 `factory` 的内部实现；调用 `Resolve` 的生成 `Aop()` 见 [生成器产物](../../01_生成的API/index.md)。
