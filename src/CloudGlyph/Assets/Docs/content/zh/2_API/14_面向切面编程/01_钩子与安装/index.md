# 钩子与安装

三阶段钩子模型与从代理出发的安装器。命名空间 `VeloxDev.AspectOriented`。

## VeloxDev.AspectOriented

### 委托：ProxyHandler

切面的一个阶段。

**签名：** `public delegate object? ProxyHandler(object?[]? parameters, object? previous)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameters` | `object?[]?` | getter 收到 `null`；setter 收到一个元素，即被写入的值；方法收到自身参数。 |
| `previous` | `object?` | 前一阶段的返回值；`start` 时为 `null`。 |

**返回：** `start` 返回传给下一阶段作为 `previous` 的值；`coverage` 返回成员结果；`end` 的返回值被丢弃。

### 类：AspectHooks

共同安装在一个成员上的三个阶段。

**签名：** `public sealed class AspectHooks(ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end)`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Start` | `ProxyHandler?` | 在成员之前运行；其返回值成为下一阶段的 `previous`。 |
| `Coverage` | `ProxyHandler?` | 非空时替换成员：成员主体不运行，此返回值即成员结果。 |
| `End` | `ProxyHandler?` | 在成员之后运行；返回值被丢弃。 |

钩子集整体安装。无法保留一个阶段而替换另一个；传入 `null` 集清除该成员的切面。

### 接口：IAopHookTarget

每个生成代理实现的安装表面。通常经 `ProxyEx.SetProxy` 调用，而非手工。

**签名：** `public interface IAopHookTarget`

| 成员 | 签名 | 说明 |
|---|---|---|
| `SetHooks` | `void SetHooks(string memberKey, AspectHooks? hooks)` | 安装或清除一个成员的切面。键为 `get_Name`、`set_Name` 或方法自身名称。 |

**异常：** `memberKey` 不是被代理类型成员时抛 `ArgumentOutOfRangeException`。

### 枚举：ProxyMembers

切面安装到哪个访问器。

**签名：** `public enum ProxyMembers`

| 成员 | 含义 |
|---|---|
| `Getter` | 属性 getter。 |
| `Setter` | 属性 setter。 |
| `Method` | 方法。 |

属性的 getter 与 setter 是独立成员，接受各自的切面。

### 类：ProxyEx

在生成的 `Aop()` 返回的代理上安装切面。

**签名：** `public static class ProxyEx`

| 成员 | 签名 | 说明 |
|---|---|---|
| `SetProxy<T>` | `static void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : IAspectOriented` | 在一个成员上安装三个阶段。`memberType` 选择 `get_` / `set_` / 裸名称。 |

**异常**

| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | `target` 是原对象而非代理。装在原对象上永不运行，因此被拒绝而非忽略。 |
| `ArgumentOutOfRangeException` | `memberName` 不是被代理类型的可拦截成员。 |

对同一成员安装两次会**替换**三个阶段。

## 示例

```csharp
using System;
using VeloxDev.AspectOriented;

var counter = new CounterViewModel();
var proxy = counter.Aop();

// 读取之前。
proxy.SetProxy(ProxyMembers.Getter, nameof(CounterViewModel.Value),
    (parameters, previous) => { Console.WriteLine("[getter before]"); return null; },
    null,
    null);

// 写入之后。
proxy.SetProxy(ProxyMembers.Setter, nameof(CounterViewModel.Value),
    null,
    null,
    (parameters, previous) =>
    {
        Console.WriteLine($"[setter after] {parameters?[0]}");
        return null;
    });

// 替换方法主体。
proxy.SetProxy(ProxyMembers.Method, nameof(CounterViewModel.Reset),
    null,
    (parameters, previous) => { Console.WriteLine("[reset replaced]"); return null; },
    null);

Console.WriteLine($"read: {proxy.Value}");
proxy.Value = 7;
proxy.Reset();
```

## 说明

- `start` 可通过返回一个准备好的对象与 `coverage` 共享状态；`coverage` 以 `previous` 收到它。忽略 `previous` 的 `coverage` 仍然替换主体。
- 对 `void` 方法，`coverage` 的返回值被忽略。
- 处理器按设计装箱。这正是生成代理无需反射与运行期代码生成的原因。
- 装在 `counter`（原对象）上的切面会被拒绝；该检查先于任何键解析。
