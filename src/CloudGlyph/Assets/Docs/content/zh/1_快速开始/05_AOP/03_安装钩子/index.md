# 安装钩子

## 取得代理

```csharp
var proxy = counter.Aop();
```

`Aop()` 按目标类生成。它调用 `AopCache.Resolve<Counter, Counter_AopQuickStart_Aop>(instance, factory)`，所以同一实例反复调用返回**同一个**代理，不同实例各得一个代理。

**预期结果：** `proxy` 的类型是生成的接口；按引用比较 `counter.Aop() == counter.Aop()` 为 `true`。

## 挂接一组钩子

`ProxyEx.SetProxy` 接收成员类别、成员裸名与三个处理器：

```csharp
proxy.SetProxy(ProxyMembers.Method, nameof(Counter.Add),
    (parameters, previous) =>
    {
        Console.WriteLine($"[start] Add({parameters?[0]}, {parameters?[1]}) called");
        return null;
    },
    (parameters, previous) =>
    {
        Console.WriteLine("[coverage] original Add() body is skipped");
        return (object?)((int)(parameters?[0] ?? 0) + (int)(parameters?[1] ?? 0));
    },
    (parameters, previous) =>
    {
        Console.WriteLine($"[end] Add() returned {previous}");
        return null;
    });
```

`ProxyMembers.Getter` 与 `ProxyMembers.Setter` 分别寻址属性的两个访问器；`ProxyMembers.Method` 寻址方法。对同一成员再次安装会**替换**整组钩子 —— 不会叠加。

## 各阶段的入参

| 阶段 | `parameters` | `previous` |
|---|---|---|
| `start` | getter：`null`；setter：`new object?[] { value }`；方法：其参数，无参数时为 `null` | `null` |
| `coverage` | 同 `start` | `start` 的结果 |
| `end` | 同 `start` | 成员结果（或 `coverage` 结果）；`void` 成员为 `null` |

只有 `coverage` 的结果会被返回。`start` 与 `end` 的返回值被忽略；即使是 `void` 成员，`end` 也会在成员体（或 `coverage`）之后运行。

**预期结果：** 三元组被存入代理上该成员的 `AspectHooks` 字段；目标实例上不发生分配或注册。

## 反向读回目标

```csharp
var original = Aop.GetTarget<Counter>(proxy);
```

**预期结果：** `original` 就是那个 `Counter` 实例；生成的工厂已通过 `Aop.Map(proxy, target)` 登记。

## 可触发的错误

| 情形 | 结果 |
|---|---|
| 在原始对象而非 `Aop()` 结果上调用 `SetProxy` | `InvalidOperationException` —— 装在那里的切面永远不会运行 |
| 未知成员名 | `IAopHookTarget.SetHooks` 抛出 `ArgumentOutOfRangeException` |
| 处理器抛异常 | 异常传播给代理调用方，后续阶段被跳过 |
| `coverage` 对值类型成员返回 `null` | 生成的拆箱转换处抛 `NullReferenceException` |
