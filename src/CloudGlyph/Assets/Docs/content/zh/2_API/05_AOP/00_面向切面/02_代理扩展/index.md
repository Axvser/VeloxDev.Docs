# AOP 运行时 — `ProxyEx`（静态类）

`Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`。它声明 `ProxyMembers` 与唯一的公开注册方法 `SetProxy`。这里没有 `CreateProxy`：代理是生成的类，由生成的 `Aop()` 扩展构造。

## ProxyEx.SetProxy\<T\>

**签名：**

```csharp
public static void SetProxy<T>(
    this T target,
    ProxyMembers memberType,
    string memberName,
    ProxyHandler? start,
    ProxyHandler? coverage,
    ProxyHandler? end)
    where T : IAspectOriented
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `target` | `T` | `Aop()` 返回的代理。传原始对象会被拒绝。 |
| `memberType` | `ProxyMembers` | `Getter`、`Setter`、`Method` —— 用于构造拦截键 |
| `memberName` | `string` | 成员裸名，如 `nameof(TeamViewModel.Name)` |
| `start` | `ProxyHandler?` | 成员之前运行，或 `null` |
| `coverage` | `ProxyHandler?` | 非空时替换成员，或 `null` |
| `end` | `ProxyHandler?` | 成员之后运行，或 `null` |

**返回：** `void`

**异常：**

| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | `target` 不是 `IAopHookTarget`，即不是生成的代理 |
| `ArgumentOutOfRangeException` | 构造的键与被代理类型的任何可拦截成员都不匹配 |

### 行为

1. 拒绝非代理目标。该检查是必要的，因为 `IAspectOriented` 是谁都能实现的空标记；装在手写实现上的切面永远不会运行。
2. 构造键：`"get_" + memberName`、`"set_" + memberName` 或 `memberName`。
3. 调用 `IAopHookTarget.SetHooks(key, new AspectHooks(start, coverage, end))`。

通过本方法无法传入整体 `null` —— 三个实参总会构造出一个 `AspectHooks`。全 `null` 的钩子组（`null, null, null`）会让成员体不带钩子地运行，但成员的槽位仍非空，因此仍走钩子路径；只有 `IAopHookTarget.SetHooks(key, null)` 能真正清空槽位。

对同一成员安装两次会**替换**前一组，不会叠加。

Demo 用法，`Examples/AOP/WPF/Demo/MainWindow.xaml.cs`（`ConfigureAOP`）：

```csharp
var p = data.Aop();

p.SetProxy(ProxyMembers.Getter,
    nameof(TeamViewModel.Name),
    (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
    null,
    null);

p.SetProxy(ProxyMembers.Method,
    nameof(TeamViewModel.Reset),
    null,
    (_, _) => { MessageBox.Show($"the default Reset() has been cancelled"); return null; },
    null);
```

**备注：**

- `target` 必须是 `Aop()` 返回的对象。编译期保护只覆盖用户类：它不实现 `IAspectOriented`，因此在原始目标上调用 `counter.SetProxy(...)` 无法满足约束。手写实现则能编译通过，并在运行期被拒绝。
- 注册与线程亲和性无关；生成的代理为每个成员保存一个字段。

相关页面：[钩子契约](../01_代理成员处理器/index.md) 描述委托与钩子组；[生成的代理](../03_生成的代理/index.md) 消费它们；[Aop 与 AopCache](../04_代理生命周期/index.md) 提供代理。
