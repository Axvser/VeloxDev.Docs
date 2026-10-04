# 过渡动画 — 抽象层：属性路径

命名空间 `VeloxDev.TransitionSystem.Abstractions`（源：`TransitionSystem/Binding/TransitionProperty.cs`、`Binding/PathSegment.cs`、`Binding/PathIndex.cs`）。一个可动画值如何被寻址、路径如何被用作字典身份，以及拒绝一条永远无法动画的路径的两个守卫。构建器与状态容器见 [builder](../00_构建器/index.md)，引擎见 [engine](../01_引擎/index.md)。

### 类：`TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>
{
    public TransitionProperty(IEnumerable<PropertyInfo> segments);   // 空 / 含索引属性时抛异常
    public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
    public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static TransitionProperty Combine(TransitionProperty prefix, TransitionProperty suffix);
    public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);

    public string Path { get; }
    public Type PropertyType { get; }
    public bool CanRead { get; }
    public bool CanWrite { get; }

    public static readonly object UnreadablePath;

    public object? GetValue(object? target);
    public bool SetValue(object target, object? value);
    public bool IsDescendantOf(TransitionProperty other);
    // + IEquatable<TransitionProperty>：Equals / GetHashCode / ToString() == Path
}
```

| 成员 | 说明 |
|---|---|
| 构造函数 | 从属性分段链构建；`segments` 为空或含索引属性时抛 `ArgumentException`（索引器需要它的实参 —— 请写进表达式）。 |
| `FromProperty` | 把一个 `PropertyInfo` 包成单段路径；null 时抛 `ArgumentNullException`。**带记忆**：同一个 `PropertyInfo` 永远产出同一个共享实例。 |
| `Members` | 从表达式声明可动画成员路径（供 `ISampleable.GetAnimatableMembers`）；只保留既**可读又可写**的成员。 |
| `ReadableMembers` | 只声明可读成员路径 —— 供**结构体** `ISampleable` 装配，那里成员只被读取并经由构造函数重建，因此不可写成员无妨。 |
| `Combine` | 拼接两条路径 —— `prefix = target.Foo`、`suffix = Foo.Bar` → `target.Foo.Bar`。 |
| `TryCreate` | 把 lambda 解析为 `TransitionProperty` —— 属性分段、数组元素、索引器与索引表达式都支持；对这条遍历描述不了的表达式返回 `false`（中间有方法调用、索引实参没有稳定身份），而不是截断路径，因为被截断的身份会让两条不同的路径撞进同一个字典条目。 |
| `UnreadablePath` | 当中间对象的运行时类型与路径不符时 `GetValue` 返回的哨兵。调用方跳过此类属性，而不是把它们当 `null` 插值。 |

**说明：**
- 一条路径是**属性分段与索引分段**的链，两者都参与身份。相等性把属性分段按**名字 + 声明类型**比较，而不是按它的 `PropertyInfo` 实例（反射在接口/实现拆分下不保证该引用稳定），索引分段则按其索引实参；`GetHashCode` 遵循同一规则，因此 `HashSet` 或字典会把相等的路径保留为一条条目。`IsDescendantOf` 用它来检测父/子路径对。`Path` / `ToString()` **仅供诊断** —— 两条相等的路径在同一条索引用不同 lambda 形参名书写时可以渲染得不同。
- 身份中没有任何东西依赖目标，且**不考察可访问性**：路径只以其末端成员是否可读可写来判定，绝不以它多可访问来判定。`private set` 与 `internal` 成员照样动画，`FromProperty` 接受你能拿到的任何 `PropertyInfo` —— 这是刻意的，因为收窄它会让今天能用的动画静默停掉。可写性只问**最后一段**：不能赋值的索引器就是普通的只读成员，而值类型位于路径**更早**处是无害的（经它到达的引用仍指向真实对象），但**末端**成员若声明在值类型上则不可写（读取得到的是副本，赋值落在临时对象里）。
- getter 与 setter 在首次使用时被编译成单个委托（`CompileGetter` / `CompileSetter`），消除逐帧反射 —— 这是 `SamplerSet.Apply` 与 `host.Run` 的热路径。编译后的访问器把索引实参当作运行时数组接收，而不是把它们烘进表达式，因此冻结一个实参不需要每次动画一次 `Reflection.Emit`。`Expression.MakeIndex` 在索引越界时**抛异常**，所以编译出的体把导航包在 `try/catch` 里，把 `IndexOutOfRangeException` / `ArgumentOutOfRangeException` / `KeyNotFoundException` 映射为调用方本就预期的静默结果（getter 为 `UnreadablePath`、setter 为 `false`），而不是从 `Prepare` 抛出、然后每帧再抛一次 —— 而且是在 UI 线程的 dispatcher 回调里，那里无人捕获。
- `FromProperty` 的记忆化是让反射驱动的入口保持廉价的关键：主题系统在**每次**切换时为每个已注册目标的每个主题化属性重建一条路径，而一个新实例会各自编译自己的 getter 与 setter（实测：一千个双属性元素，在首帧之前约两秒 UI 线程停顿）。它存放在以 `PropertyInfo` 为弱键的 `ConditionalWeakTable` 里，因为条目是一条强链 —— 路径 → 分段 → `PropertyInfo` → `Type` → `Assembly` —— 强键会把程序集钉住整个进程，可回收的 `AssemblyLoadContext` 就永远卸载不掉。
- *核验：* `TransitionPropertyTests`、`TransitionPropertyIndexerTests`。

### 静态类：`PathIndex`（命名空间 `VeloxDev.TransitionSystem`）

```csharp
public static class PathIndex
{
    public static T Frozen<T>(T value);   // 永不执行 —— 解析器识别该调用并解包
}
```

**说明：** 一条路径可以携带索引实参（`x.Items[0].Width`、`x.Map["player"].Color`、`x.Cells[1, 2]`），它们分两档。实参是路径**身份**的一部分，不是值的一部分：`x => x.Items[idx].Width` 不管 `idx` 是什么都解析成一条路径，这就是为什么一个循环用五个捕获的局部变量声明五条路径会得到五个条目。默认实参是**活**的：能在动画运行期间改变的那种 —— 捕获的局部变量，或目标自身的属性如 `x.SelectedIndex` —— 每帧重新求值，因此路径会跟随它。`Frozen` 改为把实参钉在一个槽位上，在 `Prepare` 中解析一次。凡是**终值必须落在它被读取的那个槽位**的场合都要冻结：终值在运行开始时读一次，因此中途移动的活路径会把一个对着它起步时槽位算出的终值写下去。标记是路径身份的一部分，所以 `Items[i]` 与 `Items[Frozen(i)]` 是两条不同的路径 —— 而常量实参根本不需要标记（`[0]` 与 `[Frozen(0)]` 是同一条路径，怎么写都已被钉死）。只有冻结的实参才会被包装，且只对用它的那一趟，因此无索引路径零开销。
- *核验：* `TransitionPropertyIndexerTests`（`APlainIndexFollowsTheTarget`、`AFrozenIndexStaysWhereItStarted`、`AFrozenIndexIsNotTheSamePathAsALiveOne`、`PrepareFreezesTheIndexBeforeAnyFrameIsWritten`、`PrepareLeavesAPlainIndexFollowing`）。

### 路径校验

引擎里不再有捕获 / 发现 API：动画状态逐路径声明，唯一的路径机械就是下面两个守卫。`TransitionProperty.IsDescendantOf` 实现第一个，`TransitionCore.RejectUnsampleablePaths`（internal，由 `CoreValidate` 调用）实现第二个。

- **`TransitionPathConflictException`** —— 在过渡构建期间由 `StateCore.SetValue` 抛出，当新来的路径位于其上已有路径之上或之下时（一个对象必须由且只由一条路径表达；重复加同一条路径只是普通覆盖）。只覆盖一次过渡的值路径。*核验：* `TransitionPathConflictTests`。
- **`TransitionPathUnsampleableException`** —— 由 `Transition<T>.Execute` 同步抛出，当一条声明路径永远无法动画时（末端为引用类型，既无自定义插值器也无注册采样器）。值类型豁免。*核验：* `TransitionPathValidationTests`。

两者的完整契约记录在 [transitionsystem/sampling-capture](../../00_transitionsystem/00_采样与捕获/index.md)。
