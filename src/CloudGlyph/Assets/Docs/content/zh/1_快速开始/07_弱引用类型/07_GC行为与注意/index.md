# 弱引用类型 — GC行为与注意

四个类型都存*弱*引用，因此其内容由垃圾回收器支配。本页汇总使用前必须先内化的规则；代码来自 `Src/Core/VeloxDev.Core/WeakTypes/`。

## 1. 每个类型存的是什么

| 类型 | 底层存储 |
|---|---|
| `WeakQueue<T>` | `Queue<WeakReference<T>>` |
| `WeakStack<T>` | `Stack<WeakReference<T>>` |
| `WeakDelegate<TDelegate>` | `List<WeakReference<Delegate>>` **外加**一个已缓存组合委托（`_combinedDelegate`，volatile） |
| `WeakCache<TTargetKey, TCacheKey>` | `ConditionalWeakTable<TTargetKey, TCacheKey>` **外加**一个簿记 `List<WeakReference<TTargetKey>>` |

以上都没有把条目保活。`WeakReference<T>` 不会让目标存活 —— 它只是让你能观察目标是否还在，在时把它取回。

**预期结果：** 你能说出每个类型背后的确切存储，以及哪里是弱的。

## 2. 访问时清扫

死条目不会在后台被主动删除；它们在你触碰集合时才被清扫：

- `WeakQueue<T>.Count`（因此 `IsEmpty` 亦然）先执行 `Prune()`，只报告存活条目。
- `TryDequeue` / `TryPeek`（以及栈的 `TryPop` / `TryPeek`）循环丢弃队首/栈顶的死条目，直到遇到存活的；若一个都没有，返回 `false` 与 `out null`。
- `GetEnumerator()` 先剪除，只产出存活条目。
- `WeakDelegate<TDelegate>` 在 `RebuildCache` 内清理已回收弱条目（以 `CanUpdateCache: true` 调用 `Add`/`Remove`、缓存为空的 `GetInvocationList`，或 `Clone`）。
- `WeakCache<TTargetKey, TCacheKey>` 的行在键死亡时自动从条件弱表消失；簿记 `WeakReference<TTargetKey>` 列表由 `ForeachCache` 清扫，也由 `AddOrUpdate` 在插入计数越过清理阈值时定期清扫。

**预期结果：** 你能预测死条目会在下一次读取该集合时“消失”，而不是更早。

## 3. 回收发生在 GC 时，而不是访问时

弱条目不会在最后一个强引用离开作用域的那一瞬间死亡。目标只在下一轮 GC 运行时才被回收。在那之前，弱引用仍可能报告目标存活，`Count` 仍把它数进去。这正是 [验证与完整代码](../08_验证与完整代码/)页的示例要在读取集合前强制一次 GC 的原因；生产环境里你只需让 GC 按自己的节奏运行。

**预期结果：** 你理解“弱”意味着*可回收*，而不是*立即消失*。

## 4. 如何让 GC 示例可复现

“验证与完整代码”页那个可运行程序通过刻意设计存活期来稳定地观察驱逐：

- 每个要被回收的对象都**在辅助方法内部**创建（`FillQueue`、`FillStack`、`AddDeadHandler`、`AddDeadCacheEntry`），这些方法的栈帧在 GC 之前就已返回，因此对象的唯一剩余引用就是集合里的弱引用。
- 每个要存活的对象都在 `Main` 中创建，并在末尾用一次 `GC.KeepAlive` 调用钉住。
- 一个 `ForceGc` 辅助函数执行两次完整回收，中间等待终结器：

```csharp
private static void ForceGc()
{
    GC.Collect();
    GC.WaitForPendingFinalizers();
    GC.Collect();
}
```

`WaitForPendingFinalizers` 只在对象带终结器时才要紧（示例 `Payload` 没有）；随后的第二次 `Collect` 会回收终结器阶段释放的任何东西。请用 `dotnet run -c Release` 且不要附加调试器运行。

**预期结果：** 每次 `Release` 运行回收的都是同一批对象 —— [验证与完整代码](../08_验证与完整代码/)页里的记录输出是稳定的。

## 5. Debug 与 Release 及其它注意事项

- **Debug / 附加了调试器。** 在调试器下，或 Debug 构建里，JIT 可能把局部变量保活到其外层作用域结束，于是你以为已“死”的对象可能仍被报告为存活。这就是 GC 演示要在 `Release` 下运行的原因。
- **驻留字符串。** 字符串字面量被运行时驻留，在整个进程生命周期内一直可达。`WeakCacheTests.cs` 使用诸如 `"key1"` 的键，因此那些条目永远不会被驱逐；测试断言的是 API 行为而非 GC 驱逐。想观察驱逐，请用新分配的、对象形态的键（例如本快速入门里的 `Payload`）。
- **弱列表仍需要一个重建触发点。** 在 `WeakDelegate<TDelegate>` 中，已缓存组合委托强引用每个并入它的处理器。订阅者只有在不在当前缓存中时才会被回收 —— 请以 `CanUpdateCache: false` 添加，或确保之后的重建/`Clone` 会丢弃它（见[弱委托订阅](../03_弱委托订阅/)）。
- **不要把正确性建立在 GC 时序上。** 用弱集合来*避免泄漏*，绝不要用它实现“延迟后恰好触发一次”之类的逻辑 —— 回收时序是运行时实现细节。

**预期结果：** 你能向评审者解释：为什么弱集合的结果在 Debug 与 Release 之间不同、为什么单元测试从不断言驱逐、以及为什么存在 `CanUpdateCache: false`。
