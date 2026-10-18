# 弱引用类型 — GC 行为

四个类型都存放*弱*引用，因此其内容受垃圾回收器支配。本页汇总使用前必须内化的规则；代码来自 `Src/Core/VeloxDev.Core/WeakTypes/`。

## 1. 每个类型存放什么

| 类型 | 底层存储 |
|---|---|
| `WeakQueue<T>` | `Queue<WeakReference<T>>` |
| `WeakStack<T>` | `Stack<WeakReference<T>>` |
| `WeakDelegate<TDelegate>` | `List<WeakReference<Delegate>>` **加上**缓存的组合委托（`_combinedDelegate`，volatile） |
| `WeakCache<TTargetKey, TCacheKey>` | `ConditionalWeakTable<TTargetKey, TCacheKey>` **加上**记账用的 `List<WeakReference<TTargetKey>>` |

这些*弱*存储都不会 root 条目。`WeakReference<T>` 不让目标存活——它只让你观察目标是否还存在，并在存在时取回它。本功能中唯一的强引用是 `WeakDelegate` 缓存的组合委托：并入其中的每个处理器在重建把它排除前都保持可达（见第 5 节）。

**预期结果：** 你能说出每个类型背后的确切存储，并指出哪一部分是弱的。

## 2. 访问时清扫

死条目不会由后台线程立即移除；它们在你触碰集合时被清扫：

- `WeakQueue<T>.Count`（因此 `IsEmpty`）先运行 `Prune()`，所以只报告存活条目。
- `TryDequeue` / `TryPeek`（以及栈的 `TryPop` / `TryPeek`）循环丢弃队首/栈顶的死条目，直到遇到存活条目；若没有则返回 `false` 且 `out null`。
- `GetEnumerator()` 先剪除，再只产出存活条目。
- `WeakDelegate<TDelegate>` 在 `RebuildCache` 内清理已回收的弱条目（带 `CanUpdateCache: true` 的 `Add`/`Remove`、缓存为空时的 `GetInvocationList`，或 `Clone`）。
- `WeakCache<TTargetKey, TCacheKey>` 的行在键死亡时自动从条件弱表消失；记账用的 `WeakReference<TTargetKey>` 列表由 `ForeachCache`、`Remove`，以及插入计数器越过清理阈值时的 `AddOrUpdate` 清扫。

**预期结果：** 你能预测死条目在“下次读取集合时”消失，而不是更早。

## 3. 回收发生在 GC，而不是访问时

弱条目不会在其最后的强引用离开作用域的那一刻死亡。只有下一次 GC 运行时目标才被回收。在此之前，弱引用可能仍报告目标存活，`Count` 仍会计入它。这就是完整代码页的示例在读取集合前强制 GC 的原因；生产中只需让 GC 按自己的节奏运行。

**预期结果：** 你理解“弱”意味着*可回收*，而不是*立即消失*。

## 4. 让 GC 演示可确定

完整代码页的可运行程序通过刻意塑造生命周期来稳定观察驱逐：

- 所有应被回收的对象都在**辅助方法**（`FillQueue`、`FillStack`、`AddDeadHandler`、`AddDeadCacheEntry`）内创建，其栈帧在 GC 前已返回，因此对象仅剩的引用就是集合中的弱引用。
- 所有应存活的对象都在 `Main` 中创建，并在末尾用 `GC.KeepAlive` 钉住。
- `ForceGc` 辅助方法执行两次完整回收，中间等待终结器：

```csharp
private static void ForceGc()
{
    GC.Collect();
    GC.WaitForPendingFinalizers();
    GC.Collect();
}
```

`WaitForPendingFinalizers` 只在对象有终结器时才有意义（示例 `Payload` 没有）；第二次 `Collect` 回收终结器阶段释放的任何东西。在 GC 之前让辅助方法帧返回，可使 Debug 与 Release 下的结果都稳定。

**预期结果：** 每次运行都回收相同的条目——完整代码页的记录输出是稳定的。

## 5. Debug 与 Release 及其它注意事项

- **Debug / 附加调试器。** 在调试器下或 Debug 构建中，JIT 可能把局部变量保活到其作用域结束，因此你*以为*已死的对象可能仍被报告为存活。这就是 GC 演示偏好 Release 构建且不附加调试器的原因；示例程序通过把每个待死对象都创建在帧已返回的辅助方法中来规避这一差异。
- **驻留字符串。** 字符串字面量被运行时驻留，整个进程期间保持可达。`WeakCacheTests.cs` 使用 `"key1"` 之类的键，因此那些条目永不驱逐；测试断言的是 API 行为而非 GC 驱逐。要观察驱逐，请使用新分配的对象键（如本快速开始中的 `Payload`）。
- **弱列表仍需要重建触发。** 在 `WeakDelegate<TDelegate>` 中，缓存的组合委托强引用并入其中的每个处理器。以 `CanUpdateCache: false` 添加的订阅者只在下次重建前可回收：若它在重建前死亡就被丢弃；若仍存活，重建会把它并入新的强缓存，它便一直被 root 到某次移除（见弱委托页）。
- **不要基于 GC 时机构建正确性。** 用弱集合来*避免泄漏*，绝不要用来实现“延迟后恰好触发一次”之类的逻辑——回收时机是运行时的实现细节。

**预期结果：** 你能向评审解释：为什么弱集合的结果在 Debug 与 Release 下不同、为什么单测从不断言驱逐，以及 `CanUpdateCache: false` 为何存在。
