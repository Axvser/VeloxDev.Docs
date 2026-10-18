# AOP 运行时 — 生成的代理类

真正执行拦截的不是库里的类型：`AopSurface` 把它发射进消费方程序集。其形态由 `AopSurface.WriteProxy`（`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`）固定；构建后可在测试工程的 `obj/.../generated/` 目录检查发射结果。

## 形态

对 `AopFixture`（`Src/Core/VeloxDev.Core.Test/AspectOriented/AopFixture.cs`），生成文件 `AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy.g.cs` 的开头是：

```csharp
namespace VeloxDev.AopInterfaces;

internal sealed class AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy : AopFixture_VeloxDev_Core_Test_AspectOriented_Aop
{
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Add;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Ping;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Echo;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_get_Title;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_set_Title;

    private readonly global::VeloxDev.Core.Test.AspectOriented.AopFixture _target;

    internal AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(global::VeloxDev.Core.Test.AspectOriented.AopFixture target) => _target = target;
```

每个可拦截访问器对应一个 `AspectHooks?` 字段，键与 `SetProxy` 构造的键相同。构造函数是 `internal`；只有生成的 `Aop()` 扩展会构造它。

## 快速路径 —— 无钩子

每个成员都先做空检查：

```csharp
public int Add(int a, int b)
{
    var h = _hooks_Add;
    if (h is null)
    {
        return _target.Add(a, b);

    }
    // ...
}
```

没有钩子时直接调用目标。不分配数组、不装箱、不使用反射。这就是从未注册的成员的成本。

## 钩子路径

**有返回值的方法：**

```csharp
var args = new object?[] { a, b };
var r0 = h.Start?.Invoke(args, null);
object? r1;
if (h.Coverage is null)
{
    r1 = _target.Add(a, b);
}
else
{
    r1 = h.Coverage.Invoke(args, r0);
}

h.End?.Invoke(args, r1);
return (int)r1!;
```

**无参数方法**传入 `object?[]? args = null;`，不分配空数组。

**`void` 方法**执行同样的阶段，`Coverage` 为 `null` 时置 `r1 = null`，调用 `End`，不返回值。因此 `void` 成员的 `end` 总是收到 `null`。

**属性 getter** 把参数数组传为 `null`：

```csharp
var r0 = h.Start?.Invoke(null, null);
var r1 = h.Coverage is null
    ? (object?)_target.Title
    : h.Coverage.Invoke(null, r0);
h.End?.Invoke(null, r1);
return (string)r1!;
```

**属性 setter** 传入 `new object?[] { value }`；`Coverage` 为 `null` 时先写 `_target.Property = value` 再运行 `end`，且不返回值。

## `SetHooks` 分发

```csharp
void global::VeloxDev.AspectOriented.IAopHookTarget.SetHooks(string memberKey, global::VeloxDev.AspectOriented.AspectHooks? hooks)
{
    switch (memberKey)
    {
        case "Add": _hooks_Add = hooks; return;
        case "Ping": _hooks_Ping = hooks; return;
        case "Echo": _hooks_Echo = hooks; return;
        case "get_Title": _hooks_get_Title = hooks; return;
        case "set_Title": _hooks_set_Title = hooks; return;
        default:
            throw new global::System.ArgumentOutOfRangeException(nameof(memberKey), memberKey, "not an interceptable member of VeloxDev.Core.Test.AspectOriented.AopFixture");
    }
}
```

该方法是显式接口实现，不属于代理的公开面。

## 异常

| 情形 | 结果 |
|---|---|
| `Start` / `Coverage` / `End` 抛异常 | 原样传播；后续阶段被跳过 |
| `Coverage` 对值类型成员返回 `null` | 生成的拆箱 `(T)r1!` 抛 `NullReferenceException` |
| `Coverage` 返回错误类型 | 同一转换处抛 `InvalidCastException` |
| 目标成员抛异常 | 原样传播 —— **不会**像旧的反射设计那样包成 `TargetInvocationException` |

## 线程

代理没有锁。`AspectHooks` 不可变，成员每次调用只读一次钩子字段（`var h = _hooks_Add;`），因此并发的 `SetProxy` 影响后续调用而不是进行中的调用。若被拦截成员会并发调用，钩子委托自身必须线程安全。
