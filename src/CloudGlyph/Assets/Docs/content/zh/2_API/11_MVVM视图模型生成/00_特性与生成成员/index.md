# 特性与生成成员

两个生成器触发点及它们产出的成员。这里的运行时类型都在 `VeloxDev.MVVM`；生成的成员加到你的分部类上。

## VeloxDev.MVVM

### 类：VeloxPropertyAttribute

把字段或 `partial` 属性标记为生成器要转成通知属性的成员。

**签名：**
`public class VeloxPropertyAttribute : Attribute`

**特性用法：** `AttributeTargets.Field | AttributeTargets.Property`，`AllowMultiple = false`，`Inherited = false`。

**`[VeloxProperty] private int _priority;` 生成的成员**

| 成员 | 种类 | 说明 |
|---|---|---|
| `Priority` | 属性 | 由 `_priority` 派生名称；含 getter 与 setter |
| `OnPriorityChanging(int oldValue, int newValue)` | `partial void` | 赋值前调用 |
| `OnPriorityChanged(int oldValue, int newValue)` | `partial void` | 赋值后调用 |

setter 比较新旧值，在声明类型尚未实现时触发 `PropertyChanging` / `PropertyChanged`，并把两个值传给两个分部钩子。字段初始化器仍然提供默认值。

对集合属性，getter 调用 `ObservableCollectionTracker.EnsureSubscribed`，因此直接赋给后备字段的集合也会被观察。

### 类：VeloxCommandAttribute

把方法标记为生成命令的主体。

**签名：**
`public sealed class VeloxCommandAttribute(string name = "Auto", bool canValidate = false, int semaphore = 1) : Attribute`

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `name` | `string` | `"Auto"` | 命令名。`"Auto"` 从方法名派生。 |
| `canValidate` | `bool` | `false` | 要求实现生成的校验分部方法。 |
| `semaphore` | `int` | `1` | 最大并发执行数。小于 1 的值被夹到 1。 |

| 属性 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 命令名。 |
| `CanValidate` | `bool` | 是否由分部方法校验可执行性。 |
| `Semaphore` | `int` | 最大并发执行数。 |

**特性用法：** `AttributeTargets.Method`，`AllowMultiple = false`，`Inherited = false`。

**接受的主体形状。** 无参数、一个任意类型的参数，或 2–15 个参数；每种情况都可带一个末尾 `CancellationToken`。返回 `void`、`Task`、`Task<T>`、`ValueTask` 或 `ValueTask<T>`。一种组合被拒绝：带 `CancellationToken` 的 `void` 方法。

**生成的成员**

| 情形 | 生成的成员 |
|---|---|
| 普通方法 | `public IVeloxCommand {Name}Command { get; }` |
| 强类型参数且不含方法类型参数 | `public IVeloxCommand<TParam, TResult> {Name}Command { get; }`（单参数）或对应元数 |
| 参数类型使用方法自身类型参数 | `public IVeloxCommand<TParam, TResult> Get{Name}Command<T>()` |
| `canValidate: true` | `private partial bool CanExecute{Name}Command(...)` |

命令对象在首次读取时惰性构建。校验器的参数镜像被标记方法的前导参数；无参数的方法收到单个 `object? parameter`。

### 类：ObservableCollectionTracker

按集合实例弱键控、幂等地订阅生成的集合处理器。

**签名：**
`public static class ObservableCollectionTracker`

| 成员 | 签名 | 说明 |
|---|---|---|
| `EnsureSubscribed` | `void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)` | 每个集合只订阅一次 `handler`；后续调用是 O(1) 查找。`collection` 不是 `INotifyCollectionChanged` 时什么都不做。 |
| `Unsubscribe` | `void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)` | 集合被替换时解绑 `handler`。跟踪记录保留，因此之后的 `EnsureSubscribed` 会重新订阅。 |

处理器按 `(Method, Target)` 身份比较而非委托引用，所以生成 getter 传入的方法组不会累积订阅。

## 生成的集合钩子

对类型为 `ObservableCollection<T>` 的属性 `Tags`，生成器声明四个分部钩子与一个通用基础设施钩子。

| 成员 | 签名 | 何时运行 |
|---|---|---|
| `OnItemAddedTo{Name}` | `partial void OnItemAddedToTags(IEnumerable<T> items)` | `Add` 与 `Replace` 添加项 |
| `OnItemRemovedFrom{Name}` | `partial void OnItemRemovedFromTags(IEnumerable<T> items)` | `Remove` 与 `Replace` 移除项 |
| `OnItemMovedIn{Name}` | `partial void OnItemMovedInTags(IEnumerable<T> items)` | `Move` |
| `OnItemsResetIn{Name}` | `partial void OnItemsResetInTags()` | `Clear` / 重置 |
| `OnCollectionChanged<T>` | `protected virtual void OnCollectionChanged<T>(string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)` | 每个动作，携带新旧项；可重写以集中处理 |

若基类已声明集合基础设施，生成器复用它而不是再声明一份。

## 示例

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "Untitled";
    [VeloxProperty] private int _priority = 1;
    [VeloxProperty] private ObservableCollection<string> _tags = new();

    partial void OnPriorityChanged(int oldValue, int newValue)
        => Console.WriteLine($"priority {oldValue} -> {newValue}");

    partial void OnItemAddedToTags(IEnumerable<string> tags)
        => Console.WriteLine($"added {string.Join(", ", tags)}");

    [VeloxCommand(canValidate: true)]
    private void Promote() => Priority++;

    private partial bool CanExecutePromoteCommand(object? parameter) => Priority < 3;
}
```

构建后，`Title`、`Priority`、`Tags` 与 `PromoteCommand` 作为普通成员存在。可运行程序见[快速开始](../../../1_快速开始/11_MVVM视图模型生成/index.md)。
