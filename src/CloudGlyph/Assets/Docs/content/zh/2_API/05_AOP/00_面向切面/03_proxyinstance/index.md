# AOP 运行时 — `ProxyInstance`

`Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs`。每个生成代理共享的唯一拦截点。`ProxyEx.CreateProxy`（见 [proxyex](../02_proxyex/index.md)）通过 `DispatchProxy.Create<T, ProxyInstance>()` 创建它，再填充其内部状态。

## 类形态

```csharp
public class ProxyInstance : DispatchProxy
{
    public static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; } = [];
    public static Dictionary<object, Guid> ProxyIDs { get; internal set; } = [];

    public ProxyInstance() { _localid = Guid.NewGuid(); ProxyInstances.Add(_localid, this); }

    internal object? _target = null;
    internal Type? _targetType = null;
    internal Guid _localid = Guid.Empty;

    internal Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>> GetterActions { get; set; } = [];
    internal Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>> SetterActions { get; set; } = [];
    internal Dictionary<string, Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>> MethodActions { get; set; } = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args) { /* 分发，见下 */ }
}
```

三张钩子表（`GetterActions`、`SetterActions`、`MethodActions`）为 `internal`；它们把分发的成员名键映射到 `ProxyEx.SetProxy` 写入的 `(start, coverage, end)` 三元组。`_target` / `_targetType` 字段分别保存被包装实例与其代理接口类型。

## ProxyInstance.ProxyInstances

**签名：** `static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; }`

| 参数 | 类型 | 说明 |
|---|---|---|
| （无） | | 静态属性 —— 全局注册表，把每个代理的本地 `Guid` 映射到它的 `ProxyInstance` |

**返回：** `Dictionary<Guid, ProxyInstance>`

**备注：** 由 `ProxyInstance` 构造函数填充（每个代理获得一个全新 `Guid`）。`ProxyEx.SetProxy` 先经 `ProxyIDs[target]` 再查这张表，以到达钩子表。

## ProxyInstance.ProxyIDs

**签名：** `static Dictionary<object, Guid> ProxyIDs { get; internal set; }`

| 参数 | 类型 | 说明 |
|---|---|---|
| （无） | | 静态属性 —— 把代理对象映射到它的本地 `Guid` |

**返回：** `Dictionary<object, Guid>`

**备注：** 由 `ProxyEx.CreateProxy` 填充。`SetProxy` 用它从作为 `target` 传入的代理解析所属 `ProxyInstance`。

## 构造函数：`ProxyInstance`

**签名：** `ProxyInstance()`

**返回：** `ProxyInstance`

**备注：** 公有无参构造函数。生成 `_localid = Guid.NewGuid()` 并把 `_localid → this` 登记进 `ProxyInstances`。它由 `DispatchProxy.Create<T, ProxyInstance>()` 调用，用户代码不会直接调用。

## ProxyInstance.Invoke

**签名：** `protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)` —— 每次被代理的接口成员调用都会由 `DispatchProxy` 转入这里。

| 参数 | 类型 | 说明 |
|---|---|---|
| `targetMethod` | `MethodInfo?` | 正在被调用的接口成员（`targetMethod.Name` 携带 `get_` / `set_` / 方法名） |
| `args` | `object?[]?` | 调用实参（装箱） |

**返回：** `object?` — `coverage` 处理器的结果，或反射出的真实成员结果（`R1`）。

### 分发规则（源码核验）

```csharp
protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)
{
    var Name = targetMethod?.Name ?? string.Empty;

    if (Name == string.Empty) return null;

    if (Name.StartsWith("get_"))
    {
        GetterActions.TryGetValue(Name, out var actions);
        var R0 = actions?.Item1?.Invoke(args, null);
        var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
        actions?.Item3?.Invoke(args, R1);
        return R1;
    }
    else if (Name.StartsWith("set_"))
    {
        SetterActions.TryGetValue(Name, out var actions);
        var R0 = actions?.Item1?.Invoke(args, null);
        var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
        actions?.Item3?.Invoke(args, R1);
        return R1;
    }
    else
    {
        MethodActions.TryGetValue(Name, out var actions);
        var R0 = actions?.Item1?.Invoke(args, null);
        var R1 = actions?.Item2 == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : actions.Item2.Invoke(args, R0);
        actions?.Item3?.Invoke(args, R1);
        return R1;
    }
}
```

行为：

- `Name` 为空 / `null` → 返回 `null`。
- 以 `get_` 开头查 `GetterActions`，`set_` 开头查 `SetterActions`，否则查 `MethodActions`。取出的 `Tuple` 解包为 `Item1 = start`、`Item2 = coverage`、`Item3 = end`。
- 未注册三元组（`TryGetValue` 失败）时 `actions` 为 `null`，成员仍会被转发到真实实例：`_targetType.GetMethod(Name).Invoke(_target, args)`。
- 注册了 `coverage` 钩子时它完全替换成员体，其返回值成为成员结果（`R1`）；非空的 `start` 返回值只作为 `previous` 喂给 `coverage`，`end` 的返回值被丢弃。

**异常：** 钩子或反射调用可能抛出异常，异常会传播给代理调用方 —— `Invoke` 内部没有 `try/catch`。

相关页面：[ProxyEx](../02_proxyex/index.md) 创建并配置此类型；[Aop 与 AopCache](../04_代理生命周期/index.md) 覆盖生命周期辅助。
