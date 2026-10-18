# AOP 运行时 — 钩子契约

四个类型定义了“能钩什么”与“钩子长什么样”：`ProxyMembers` 选择访问器，`ProxyHandler` 是委托签名，`AspectHooks` 捆绑三个阶段，`IAopHookTarget` 是生成的代理所实现的安装面。

这四个类型分别位于 `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`（枚举与 `ProxyEx`）和 `AspectHooks.cs`（委托、`AspectHooks`、`IAopHookTarget`）。

## 类型：`ProxyMembers`（枚举）

```csharp
public enum ProxyMembers
{
    Getter,
    Setter,
    Method
}
```

`ProxyEx.SetProxy` 按它构造拦截键：

| 成员 | 写入的键 | 示例 |
|---|---|---|
| `Getter` | `"get_" + memberName` | `get_Name` |
| `Setter` | `"set_" + memberName` | `set_Name` |
| `Method` | `memberName` 原样 | `Reset` |

属性的 getter 与 setter 是两个独立成员，各有独立钩子组。

## 类型：`ProxyHandler`（委托）

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameters` | `object?[]?` | getter：`null`。setter：一个元素，即写入值。方法：其参数；无参数时为 `null`。 |
| `previous` | `object?` | `start` 为 `null`；`coverage` 为 `start` 的结果；`end` 为产出的结果。 |

**返回：** `object?` —— 只有 `coverage` 的返回值会被采纳为成员结果。

**异常：** 未声明。处理器可以抛出异常；异常传播给代理调用方，后续阶段不再运行。

## 类型：`AspectHooks`（密封类）

```csharp
public sealed class AspectHooks(ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end)
{
    public ProxyHandler? Start { get; }
    public ProxyHandler? Coverage { get; }
    public ProxyHandler? End { get; }
}
```

每个成员一组。整组安装：不能只替换其中一个阶段而保留其余阶段。整组传 `null` 会清除该成员的切面（生成的 `SetHooks` 直接给字段赋值）。

## 类型：`IAopHookTarget`（接口）

```csharp
public interface IAopHookTarget
{
    void SetHooks(string memberKey, AspectHooks? hooks);
}
```

每个生成的代理显式实现它。用户代码只通过 `ProxyEx.SetProxy` 触达。

**异常：**

| 异常 | 条件 |
|---|---|
| `System.ArgumentOutOfRangeException` | `memberKey` 与被代理类型的任何可拦截成员都不匹配 |

未知键会抛异常而不是什么都不做：静默失效的切面正是这套 API 要避免的失败形态。

## 阶段顺序

对有钩子的成员，生成的代理执行：

```text
R0 = Start?.Invoke(parameters, null)
R1 = Coverage is null ? <成员自身的方法体> : Coverage.Invoke(parameters, R0)
End?.Invoke(parameters, R1)
return R1
```

`Start` 看不到结果；`Coverage` 非空时替换方法体；`End` 观察最终结果，其返回值被丢弃。`void` 成员的 `R1 == null`。

相关页面：[ProxyEx](../02_代理扩展/index.md) 安装这些钩子组；[生成的代理](../03_生成的代理/index.md) 运行它们。
