# AOP 运行时 — `Aop` 与 `AopCache`

生成的 `Aop()` 背后的两个静态辅助类。`AopCache` 为每个目标实例返回一个代理；`Aop` 把代理映射回目标。两者在关键方向上都是弱引用，因此代理与其目标会被一起回收。

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
| `proxy` | `object` | 生成的代理 |
| `target` | `object` | 它包裹的实例 |

**返回：** `void`

**异常：** 未声明。`ConditionalWeakTable.Add` 对重复键抛 `ArgumentException`；生成的工厂对每个新建代理只调用一次 `Map`，因此经 `Aop()` 不可达。

**备注：** 由生成的 `Aop()` 工厂在构造代理后立即调用。

### Aop.GetTarget\<TTarget\>

**签名：** `TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class`

| 参数 | 类型 | 说明 |
|---|---|---|
| `proxy` | `IAspectOriented` | 要反向映射的代理 |

**返回：** `TTarget?` —— 目标；代理从未被映射时返回 `null`。

**异常：** 未声明；`TTarget` 不兼容时转换抛 `InvalidCastException`。

**备注：** 摊还 `O(1)`。由 `AopProxyTests.GetTargetReversesTheProxy` 覆盖：

```csharp
Assert.AreSame(fixture, Aop.GetTarget<AopFixture>(fixture.Aop()));
```

## 类型：`AopCache`（静态类）

`Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs`：

```csharp
private static class Entry<
    TClass,
    [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicParameterlessConstructor)] TInterface>
    where TClass : class
    where TInterface : class, IAspectOriented
{
    public static readonly ConditionalWeakTable<TClass, TInterface> Instances = [];
}

public static TInterface Resolve<
    TClass,
    [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicParameterlessConstructor)] TInterface>(
    TClass instance,
    Func<TClass, TInterface> factory)
    where TInterface : class, IAspectOriented
    where TClass : class
{
    return Entry<TClass, TInterface>.Instances
        .GetValue(instance, k => factory(k));
}
```

### AopCache.Resolve\<TClass, TInterface\>

**签名：** `TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `instance` | `TClass` | 目标；缓存键 |
| `factory` | `Func<TClass, TInterface>` | 未缓存时构造代理 |

**返回：** `TInterface` —— 缓存的代理，或工厂结果（随后被存入）。

**异常：** 未声明。`factory` 抛出的异常会传播，且不缓存任何东西。

**备注：**

- 嵌套泛型 `Entry<TClass, TInterface>` 通过 CLR 泛型特化为每个 `(TClass, TInterface)` 对提供独立的 `ConditionalWeakTable`。无需按类生成缓存代码。
- `ConditionalWeakTable.GetValue` 是线程安全的：并发的首次调用可能各自执行工厂，但只有一个结果被存入并从此返回。
- 弱键是目标；只要目标存活，值就保持代理存活。测试 `AProxyIsCollectableOnceItsTargetIs` 断言丢掉目标后两者都能被回收。没有静态注册表为代理生根。
- `TInterface` 上的 `DynamicallyAccessedMembers(PublicParameterlessConstructor)` 只为满足裁剪器对 `ConditionalWeakTable` 的标注；`GetOrCreateValue` 从未被调用。具体的生成接口无需无参构造函数即可满足该标注。

相关页面：[ProxyEx](../02_代理扩展/index.md) 在返回的代理上安装钩子；[生成器产物](../../01_生成的API/index.md) 展示调用 `Resolve` 的 `Aop()` 扩展。
