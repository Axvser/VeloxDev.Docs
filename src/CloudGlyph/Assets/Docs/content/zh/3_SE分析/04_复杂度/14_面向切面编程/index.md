# 面向切面编程

代理是生成的 C#：每个目标类型一个类，每个可拦截成员一个钩子字段，以及一个按成员键分支的固定 `switch`。调用是强类型虚调用，不是反射。因此每次调用的代价是一次字段读取加可选的委托链，每实例代价是一个带 $M$ 个引用大小钩子槽的代理。

记号：类型上可拦截成员 $M$，被钩子调用的参数 $n$，已安装钩子 $k$（每成员至多三个）。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `AopCache.Resolve` | 均摊 $O(1)$ 弱表查找 | 表项 $O(1)$ | `Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs:41` |
| 代理创建（首次解析） | $O(M)$ 字段初始化 | 每代理 $O(M)$ | `Src/Generators/VeloxDev.Core.Generator/Writers/AopWriter.cs:58` |
| `Aop.Map` / `Aop.GetTarget` | 均摊 $O(1)$ | 每对 $O(1)$ | `Src/Core/VeloxDev.Core/AspectOriented/Aop.cs:19` |
| `SetProxy` | $O(1)$ switch + 键哈希 | 一个 `AspectHooks` | `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs:50` |
| 无钩子成员调用 | $O(1)$，不分配 | — | `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:251` |
| 有钩子 getter | 至多 3 次委托 + 装箱，$O(1)$ | $O(1)$ | `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:257` |
| 有钩子方法 | $O(1)$ 委托调用 + $O(n)$ 数组/装箱 | $O(n)$ | `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:310` |

## 解析是弱表，不是缓存遍历

每个封闭的 `(TClass, TInterface)` 对拥有一个静态 `ConditionalWeakTable`，所以解析是一次哈希查找，工厂只在未命中时运行：

```csharp
return Entry<TClass, TInterface>.Instances
    .GetValue(instance, k => factory(k));
```

出处：`Src/Core/VeloxDev.Core/AspectOriented/AopCache.cs:49-50`

`Aop.Map` 与 `Aop.GetTarget` 是另外两次弱表操作，每个方向一次。两张表都以弱键持有，因此代理与目标可以一起被回收，无需显式移除。

## 快路径没有反射

生成的 getter 读取钩子字段，为空时直接调用目标：

```csharp
if (_hooks_get_Name is null)
    return _target.Name;
```

出处：`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:251-255`（形态）

安装钩子后，调用变为至多三次委托调用加底层访问：

```csharp
var start = _hooks_get_Name?.Start;
var coverage = _hooks_get_Name?.Coverage;
var end = _hooks_get_Name?.End;
start?.Invoke(...);
var value = coverage is null ? _target.Name : coverage(...);
end?.Invoke(...);
return value;
```

出处：`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:257-262`（形态）

带 $n$ 个值类型参数的有钩子方法会分配一个 `object[]` 并装箱每个参数；计算属性的结果也会被装箱。无钩子时两者都不发生。

## 钩子安装是生成的 switch

`SetProxy` 构造键（`get_`/`set_` 加成员名）并把钩子交给代理；代理的生成 `SetHooks` 是对常量字符串的 `switch`：

```csharp
public void SetHooks(string memberKey, AspectHooks? hooks)
{
    switch (memberKey)
    {
        case "get_Name": _hooks_get_Name = hooks; break;
        ...
        default: throw new ArgumentOutOfRangeException(nameof(memberKey));
    }
}
```

出处：`Src/Generators/VeloxDev.Core.Generator/AopSurface.cs:336-361`（形态）

对固定成员集，字符串哈希后是 $O(1)$。安装会整体替换 `AspectHooks` 值，而不是合并单个钩子。

## 可用性与内存

AOP 运行时位于 `#if NET` 中，所以它编入 `net5.0` 与 `net8.0` 构建，但不编入 `netstandard2.0` 或 `netframework4.6.1`。这是上面所有代价的前提：在较旧目标上代理类型不存在。

每个代理的内存是一个目标引用，加上每个可拦截成员一个钩子引用；已安装的 `AspectHooks` 是三个委托引用。每个活代理有两条弱表项（实例到代理、代理到实例），可被 GC 回收；静态泛型表不持有强条目。
