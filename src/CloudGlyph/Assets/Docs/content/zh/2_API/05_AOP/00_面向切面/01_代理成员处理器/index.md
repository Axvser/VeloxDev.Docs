# AOP 运行时 — `ProxyMembers` 与 `ProxyHandler`

运行时的钩子契约。`ProxyMembers` 选择一次 `ProxyEx.SetProxy` 调用针对哪种成员注册；`ProxyHandler` 是 `start`、`coverage`、`end` 三段钩子共用的签名。

## 类型：`ProxyMembers`（枚举）

声明于 `Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`：

```csharp
public enum ProxyMembers
{
    Getter,
    Setter,
    Method
}
```

选择一次注册写入哪张钩子表。内部每个 `ProxyInstance` 维护三张表 —— `GetterActions`、`SetterActions`、`MethodActions`，按分发的成员名作键。

| 成员 | 钩子表 | 分发后的成员名键 |
|---|---|---|
| `ProxyMembers.Getter` | `GetterActions` | `get_{成员}`（如 `get_Name`） |
| `ProxyMembers.Setter` | `SetterActions` | `set_{成员}`（如 `set_Name`） |
| `ProxyMembers.Method` | `MethodActions` | 不带前缀的方法名（如 `Reset`） |

**备注：** 每张表把键映射到 `Tuple<ProxyHandler?, ProxyHandler?, ProxyHandler?>` —— 即 `(start, coverage, end)` 三元组。因此一个属性通过两条独立注册被拦截：一条 `Getter` 项（键 `get_*`）加一条 `Setter` 项（键 `set_*`）。

## 类型：`ProxyHandler`（委托）

声明于 `Src/Core/VeloxDev.Core/AspectOriented/ProxyInstance.cs`：

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

`start`、`coverage`、`end` 三段钩子共用的签名。

### Invoke

**签名：** `object? Invoke(object?[]? parameters, object? previous)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `parameters` | `object?[]?` | 被拦截成员的实参（装箱）。对 setter，`parameters[0]` 是正要写入的值；对 `AOP_OnMemberAdded`，`parameters[1]` 是 `NotifyCollectionChangedEventArgs` |
| `previous` | `object?` | 上一阶段串联下来的结果：对 `start` 为 `null`；对 `coverage` 为 start 的结果 `R0`；对 `end` 为 coverage / 反射的结果 `R1` |

**返回：** `object?` — 只有非空的 `coverage` 返回值会被作为成员结果采纳；`start` 与 `end` 的返回值当前会被分发器丢弃。

**异常：** 未声明 —— 处理器可以抛出异常，异常会穿过 `ProxyInstance.Invoke` 传播给代理调用方。

### 三段管线

对一次被代理的成员调用，分发器 —— ProxyInstance.Invoke（[proxyinstance](../03_proxyinstance/index.md)）—— 会执行：

```text
R0 = start?.Invoke(parameters, null)              // 成员体之前
R1 = coverage != null ? coverage.Invoke(parameters, R0)   // 替换成员体
                     : 反射调用真实目标成员(parameters)
end?.Invoke(parameters, R1)                        // 成员体之后
return R1
```

Demo 验证的处理器，`Examples/AOP/WPF/Demo/MainWindow.xaml.cs`（`ConfigureAOP`）：

```csharp
// start —— 在读取 Name 之前触发
p.SetProxy(ProxyMembers.Getter, nameof(TeamViewModel.Name),
    (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
    null,
    null);

// end —— 在 Name 改变之后触发；parameters[0] 是写入的新值
p.SetProxy(ProxyMembers.Setter, nameof(TeamViewModel.Name),
    null,
    null,
    (p, _) => { MessageBox.Show($"the name of team has been changed to {p?[0]}"); return null; });
```

相关页面：[ProxyEx](../02_proxyex/index.md) 注册这些钩子；[ProxyInstance](../03_proxyinstance/index.md) 分发它们。
