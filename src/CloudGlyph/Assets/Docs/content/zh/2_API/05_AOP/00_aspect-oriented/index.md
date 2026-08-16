# AOP — `VeloxDev.AspectOriented`（AOP 运行时，`#if NET`）

运行时命名空间。每个源文件都包裹在 `#if NET` 中，因此这些类型只在包的 `net5.0+` 目标上可用。

### 类型：`AspectOrientedAttribute`

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
    AllowMultiple = false, Inherited = false)]
public class AspectOrientedAttribute : Attribute { }
```

标记 `partial` 类中需要被代理拦截的方法、属性与字段。源生成器会把被标记成员暴露到生成的 AOP 接口上，并扩展该类以使其实现该接口。

#### AspectOrientedAttribute.AspectOrientedAttribute

**签名：**
`AspectOrientedAttribute()`

| 参数 | 类型 | 说明 |
|---|---|---|
| （无） | | 无参构造（该特性不携带任何状态） |

**返回：** `AspectOrientedAttribute`

**异常：** 无

**示例：**
```text
// 出处：Examples/AOP/WPF/Demo/TeamViewModel.cs
[VeloxProperty][AspectOriented] private string _name = string.Empty;
```

**备注：**
- 仅适用于 `Method`、`Property`、`Field` 目标。`AllowMultiple = false`，`Inherited = false`。
- 被标记成员必须是 `public`，生成器才会把它暴露到代理接口上（被 `[VeloxProperty]` / `[Observable]` 标记的字段会变成属性）。

### 类型：`IAspectOriented`

```csharp
public interface IAspectOriented { }
```

空的标记接口。每个生成的 AOP 代理接口都继承自它；用作 `ProxyEx.CreateProxy` / `ProxyEx.SetProxy` / `Aop.GetTarget` 的泛型约束。

**成员：** 无。

### 类型：`ProxyMembers`（枚举）

```csharp
public enum ProxyMembers { Getter, Setter, Method }
```

选择 `SetProxy` 调用写入哪张钩子表。

| 成员 | 说明 |
|---|---|
| `ProxyMembers.Getter` | 属性 getter 钩子 —— 存于 `ProxyInstance.GetterActions`，按 `get_*` 方法名匹配 |
| `ProxyMembers.Setter` | 属性 setter 钩子 —— 存于 `ProxyInstance.SetterActions`，按 `set_*` 方法名匹配 |
| `ProxyMembers.Method` | 普通方法钩子 —— 存于 `ProxyInstance.MethodActions`，按方法名匹配 |

### 类型：`ProxyHandler`（委托）

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

`start`、`coverage`、`end` 三种处理器共用的钩子签名。

#### ProxyHandler.Invoke

**签名：**
`object? Invoke(object?[]? parameters, object? previous)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameters` | `object?[]?` | 被拦截成员的实参（装箱）。对 setter，`parameters[0]` 是写入的新值 |
| `previous` | `object?` | 上一阶段串联而来的返回值：对 `start` 为 `null`；对 `coverage` 为 start 的结果 `R0`；对 `end` 为 coverage / 反射的结果 `R1` |

**返回：** `object?` — 该阶段的返回值。`coverage` 非空时其返回值替换原成员的返回结果。

**异常：** 未声明（处理器可以抛出异常；异常会穿过 `ProxyInstance.Invoke` 传播给代理调用方）。

**示例：**
```text
// 出处：Examples/AOP/WPF/Demo/MainWindow.xaml.cs
(_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; }
```

### 类型：`ProxyEx`（静态类）

工厂与钩子注册辅助类。

#### ProxyEx.CreateProxy\<T\>

**签名：**
`T CreateProxy<T>(this T target) where T : IAspectOriented`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `T` | 要包装的目标实例（生成的接口类型） |

**返回：** `T` — 一个实现 `T` 并把拦截转发给 `ProxyInstance` 的 `DispatchProxy`。

**异常：**
| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | `DispatchProxy.Create<T, ProxyInstance>()` 返回了 `null` |

**示例：**
```text
// 出处：生成的 Aop() 扩展（Writers/AopWriter.cs）
var p = ProxyEx.CreateProxy<TInterface>(x);
```

**备注：**
- 调用 `DispatchProxy.Create<T, ProxyInstance>()`，通过动态分发设置内部的 `_target` / `_targetType` 字段，并把代理登记到 `ProxyInstance.ProxyIDs`（代理 → 本地 `Guid`），以便后续 `SetProxy` 能找到它。
- 通常你应使用生成的 `Aop(this T)` 扩展，而不是直接调用 `CreateProxy`。

#### ProxyEx.SetProxy\<T\>

**签名：**
`void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : class, IAspectOriented`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `T` | 代理实例（`Aop()` 的返回值），必须已登记在 `ProxyInstance.ProxyIDs` 中 |
| `memberType` | `ProxyMembers` | `Getter` / `Setter` / `Method` —— 选择钩子表 |
| `memberName` | `string` | 不带前缀的成员名（例如 `nameof(TeamViewModel.Name)`、`nameof(TeamViewModel.Reset)`）；对属性访问器实现会自动加 `get_` / `set_` 前缀 |
| `start` | `ProxyHandler?` | 在成员体之前执行；传 `null` 跳过 |
| `coverage` | `ProxyHandler?` | 非空时替换成员体；传 `null` 回退为对真实目标做反射调用 |
| `end` | `ProxyHandler?` | 在成员体之后执行；传 `null` 跳过 |

**返回：** `void`

**异常：** 未声明。如果 `target` 不是已登记的代理，调用是静默无操作。

**示例：**
```text
// 出处：Examples/AOP/WPF/Demo/MainWindow.xaml.cs（ConfigureAOP）
p.SetProxy(ProxyMembers.Getter, nameof(TeamViewModel.Name),
    start, null, null);    // 在读取 Name [前]触发
p.SetProxy(ProxyMembers.Method, nameof(TeamViewModel.Reset),
    null, coverage, null); // 替换默认的 Reset() 逻辑
```

**备注：**
- 一次 `SetProxy` 调用写入**整个** `(start, coverage, end)` 三元组；对同一成员再次调用 `SetProxy` 会覆盖已存储的三元组。
- `target` 必须是代理（而非裸实例）；`SetProxy` 通过 `ProxyIDs` → `ProxyInstances` 定位 `ProxyInstance`。

### 类型：`ProxyInstance`（继承 `DispatchProxy`）

```csharp
public class ProxyInstance : DispatchProxy
{
    public static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; } = [];
    public static Dictionary<object, Guid> ProxyIDs { get; internal set; } = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args);
}
```

每个生成的代理共享的唯一拦截点。内部状态（`_target`、`_targetType`、`_localid`）与三张钩子表（`GetterActions`、`SetterActions`、`MethodActions`）由 `ProxyEx.CreateProxy` / `SetProxy` 设置。

#### ProxyInstance.ProxyInstances

**签名：**
`Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; }`

| 参数 | 类型 | 说明 |
|---|---|---|
| （无） | | 静态属性 —— 全局注册表，把代理的本地 `Guid` 映射到它的 `ProxyInstance` |

**返回：** `Dictionary<Guid, ProxyInstance>`

**备注：** 在 `ProxyInstance` 构造函数与 `ProxyEx.CreateProxy` 中登记。`SetProxy` 用它为给定代理查找钩子表。

#### ProxyInstance.ProxyIDs

**签名：**
`Dictionary<object, Guid> ProxyIDs { get; internal set; }`

| 参数 | 类型 | 说明 |
|---|---|---|
| （无） | | 静态属性 —— 把代理对象映射到它的本地 `Guid` |

**返回：** `Dictionary<object, Guid>`

**备注：** 由 `ProxyEx.CreateProxy` 填充。`SetPropertyGetter` / `SetPropertySetter` / `SetMethod` 用它从 `target` 参数解析 `ProxyInstance`。

#### ProxyInstance.Invoke

**签名：**
`object? Invoke(MethodInfo? targetMethod, object?[]? args)` — `protected override`，每次被代理的调用都会由 `DispatchProxy` 转入这里。

| 参数 | 类型 | 说明 |
|---|---|---|
| `targetMethod` | `MethodInfo?` | 正在被调用的接口方法 |
| `args` | `object?[]?` | 调用实参 |

**返回：** `object?` — `coverage` 处理器的结果，或反射结果，或 `end` 串联后的值。

**分发规则：**
- `targetMethod.Name` 为 `""` / `null` → 返回 `null`。
- 名字以 `get_` 开头 → 查 `GetterActions`；再以 `set_` 开头 → `SetterActions`；否则 → `MethodActions`。
- 对命中的三元组执行：`R0 = start?.Invoke(args, null)`；然后 `R1 = coverage == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : coverage.Invoke(args, R0)`；再 `end?.Invoke(args, R1)`；返回 `R1`。

**异常：** 钩子或反射调用可能抛出异常，异常会传播给代理调用方（`Invoke` 内部没有 try/catch）。

### 类型：`Aop`（静态类）

代理生命周期基础设施，提供代理 → 目标的逆向查找。

#### Aop.Map

**签名：**
`void Map(object proxy, object target)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `proxy` | `object` | AOP 代理 |
| `target` | `object` | 代理包裹的原始实例 |

**返回：** `void`

**异常：** 未声明。

**示例：**
```text
// 出处：生成的 Aop() 扩展（Writers/AopWriter.cs）
Aop.Map(p, x);   // p = 已创建的代理，x = 原始实例
```

**备注：** 把键值对存入静态的 `ConditionalWeakTable<object, object>`；由生成的 `Aop()` 扩展调用。弱表意味着该映射不会让目标存活超过其自然生命周期。

#### Aop.GetTarget\<TTarget\>

**签名：**
`TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class`

| 参数 | 类型 | 说明 |
|---|---|---|
| `proxy` | `IAspectOriented` | 要做逆向映射的 AOP 代理 |

**返回：** `TTarget?` — 原始目标实例；若代理从未被映射则返回 `null`。

**异常：** 无。

**示例：**
```text
// 出处：由运行时推断（Aop.cs）；与 demo 接线一致
var original = Aop.GetTarget<TeamViewModel>(team);
```

**备注：** 对 `ConditionalWeakTable` 做逆向查找 —— 摊还 `O(1)`。

### 类型：`AopCache`（静态类）

AOP 代理的泛型弱引用缓存。

#### AopCache.Resolve\<TClass, TInterface\>

**签名：**
`TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory) where TInterface : class, IAspectOriented where TClass : class`

| 参数 | 类型 | 说明 |
|---|---|---|
| `instance` | `TClass` | 作为缓存键的目标实例 |
| `factory` | `Func<TClass, TInterface>` | 当该实例还没有缓存代理时，用于创建代理 |

**返回：** `TInterface` — 若已缓存则返回缓存代理，否则返回 `factory` 创建并存入缓存的代理。

**异常：** 未声明。

**示例：**
```text
// 出处：生成的 Aop() 扩展（Writers/AopWriter.cs）
return AopCache.Resolve<TeamViewModel, TeamViewModel_Demo_Aop>(
    instance,
    static x => { var p = ProxyEx.CreateProxy<TeamViewModel_Demo_Aop>(x); Aop.Map(p, x); return p; });
```

**备注：**
- 利用 CLR 泛型特化，为每一对 `(TClass, TInterface)` 提供独立的 `ConditionalWeakTable<TClass, TInterface>`（`Entry<TClass, TInterface>`）——无需为每个类生成缓存代码。
- 每个目标只创建一次代理，并随目标一起被 GC 回收（弱键）。
