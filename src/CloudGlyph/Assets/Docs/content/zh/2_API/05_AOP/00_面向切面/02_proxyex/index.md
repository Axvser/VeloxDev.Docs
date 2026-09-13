# AOP 运行时 — `ProxyEx`（静态类）

`Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`。静态工厂与钩子注册辅助类。该文件同时也声明了 `ProxyMembers` 枚举（见 [ProxyMembers 与 ProxyHandler](../01_代理成员处理器/index.md)）。

## ProxyEx.CreateProxy\<T\>

**签名：** `T CreateProxy<T>(this T target) where T : IAspectOriented`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `T` | 要包装的实例。`T` 是生成的 AOP 接口类型，因此返回的代理可按该接口类型保存 |

**返回：** `T` — 一个实现 `T` 的 `DispatchProxy`，其拦截被转发给新建的 `ProxyInstance`。

**异常：**

| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | `DispatchProxy.Create<T, ProxyInstance>()` 返回了 `null` |

**实现说明：**

- 执行 `DispatchProxy.Create<T, ProxyInstance>()`；代理对应的 `ProxyInstance` 构造函数已生成本地 `Guid` 并把它登记进 `ProxyInstance.ProxyInstances`。
- 通过动态分发设置内部 `_target`（= `target`）与 `_targetType`（= `typeof(T)`，即代理接口）字段，然后把 `proxy → _localid` 登记进 `ProxyInstance.ProxyIDs`。
- 这正是生成的 `Aop()` 扩展传给 `AopCache.Resolve` 的工厂主体（`Writers/AopWriter.WriteExtension` 为 WPF demo 的 `Demo.TeamViewModel` 发射的 lambda）：

```csharp
// 出处：由 Src/Generators/VeloxDev.Core.Generator/Writers/AopWriter.cs（WriteExtension）发射
static x =>
{
    var p = global::VeloxDev.AspectOriented.ProxyEx.CreateProxy<global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop>(x);
    global::VeloxDev.AspectOriented.Aop.Map(p, x);
    return p;
}
```

**备注：** 通常应调用生成的 `Aop(this T)` 扩展而非直接使用 `CreateProxy`；见 [生成器产物](../../01_生成的API/index.md)。

## ProxyEx.SetProxy\<T\>

**签名：** `void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : class, IAspectOriented`

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `T` | 代理实例（`Aop()` / `CreateProxy` 的返回值）。它必须已登记在 `ProxyInstance.ProxyIDs` 中，否则调用是静默无操作 |
| `memberType` | `ProxyMembers` | `Getter` / `Setter` / `Method` —— 选择钩子表 |
| `memberName` | `string` | 不带 `get_` / `set_` 前缀的成员名（例如 `nameof(TeamViewModel.Name)`、`nameof(TeamViewModel.Reset)`）。属性按 `get_` / `set_` 键分发，方法按不带前缀的名字分发 |
| `start` | `ProxyHandler?` | 在成员体之前执行；传 `null` 跳过 |
| `coverage` | `ProxyHandler?` | 非空时替换成员体；传 `null` 回退为反射调用真实目标成员 |
| `end` | `ProxyHandler?` | 在成员体之后执行；传 `null` 跳过 |

**返回：** `void`

**异常：** 未声明。若 `target` 不是已登记的代理，调用是静默无操作（底层 `SetPropertyGetter` / `SetPropertySetter` / `SetMethod` 原样返回 `source`）。

**实现说明：**

- 按 `memberType` 分发到内部的 `SetPropertyGetter` / `SetPropertySetter` / `SetMethod`：它们先解析 `ProxyInstance.ProxyIDs[target]`，再经 `ProxyInstance.ProxyInstances[id]` 找到实例，把整个 `(start, coverage, end)` 三元组按分发名键写入。
- 对同一成员再次调用 `SetProxy` 会覆盖已存的三元组（`ContainsKey` 分支更新该项）。

Demo 验证的用法，`Examples/AOP/WPF/Demo/MainWindow.xaml.cs`（`ConfigureAOP`）：

```csharp
var p = data.Aop();

// 前置钩子：在读取 Name 之前触发
p.SetProxy(ProxyMembers.Getter,
    nameof(TeamViewModel.Name),
    (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
    null,
    null);

// 覆盖原始逻辑：取消默认的 Reset() 行为
p.SetProxy(ProxyMembers.Method,
    nameof(TeamViewModel.Reset),
    null,
    (_, _) => { MessageBox.Show($"the default Reset() has been cancelled"); return null; },
    null);
```

相关页面：[ProxyInstance](../03_proxyinstance/index.md) 存储并分发所注册的三元组；[Aop 与 AopCache](../04_代理生命周期/index.md) 说明 `Aop()` 的缓存机制。
