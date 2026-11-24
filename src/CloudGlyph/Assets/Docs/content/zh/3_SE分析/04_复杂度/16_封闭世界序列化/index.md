# 封闭世界序列化

序列化是带引用表的图遍历：每个不同对象只写一次，重复项变成引用号，读取器在读取成员前先登记每个实例，所以环可以解开。注册表是无锁的字典快照，因此类型派发是常数时间。不明显的代价在读侧：生成的读取器是对成员名的线性 `if / else if` 链，使成员派发对每类型成员数呈二次。

记号：不同对象 $V$，成员/边引用 $E$，对象 $v$ 的类型成员数 $k_v$，平均成员名长度 $L$，文档大小 $D$，注册类型 $W$，读取缓冲区 $B$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `Serialize` | $O(V + E)$ | 写器引用 $O(V)$ + 输出 $O(D)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:56` |
| 每对象 `WriteValue` | $O(1)$ 注册表查找 + $O(k)$ 次成员写 | — | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:136` |
| 重复对象引用 | $O(1)$ 身份哈希探测 | $O(1)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonWriter.cs:122` |
| `Deserialize` | $O(V + E + \sum_v k_v^2)$ | 读取器引用 $O(V)$ + 文档 | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:257` |
| 生成的成员派发 | 每对象 $O(k^2 L)$ | — | `Src/Generators/VeloxDev.Core.Generator/Writers/VeloxJsonCodeWriter.cs:272` |
| 注册表查找 | 均摊 $O(1)$，无锁 | 快照 $O(W)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonRegistry.cs:268` |
| 注册一个类型 | $O(W)$ 写时复制 | $O(W)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonRegistry.cs:196` |

## 写出在遇到重复引用时停止

写器在字典中保存身份引用；第二次出现时发出引用号而不是再次下降：

```csharp
if (_references.TryGetValue(instance, out var existing))
{
    WriteReference(existing);
    return false;
}

_references[instance] = _nextReferenceId++;
```

出处：`Src/Core/VeloxDev.Core/Serialization/VeloxJsonWriter.cs:126-132`

这正是循环图得以终止的原因。每个对象花费一次注册表派发加每个成员一次写，所以总计是 $O(V + E)$；引用表是 $O(V)$。

## 读取由线性名称链派发

生成的读取器循环成员，按顺序把每个名称与常量比较：

```csharp
while (reader.NextMember())
{
    if (reader.MemberNameEquals("A")) { ... }
    else if (reader.MemberNameEquals("B")) { ... }
    ...
    else reader.SkipValue();
}
```

出处：`Src/Generators/VeloxDev.Core.Generator/Writers/VeloxJsonCodeWriter.cs:272-296`（形态）

`MemberNameEquals` 就地比较、不分配字符串，但每次比较是 $O(L)$。第 $j$ 个成员要经过 $j-1$ 次失败比较后才轮到，所以一个对象最坏花费 $O(k^2 L)$ 次名称比较。除此之外读取器是线性的：

```csharp
if (!reader.BeginObject(out var referenceId, out var typeName))
    return reader.ResolveReference(referenceId);
...
var registered = VeloxJsonRegistry.ReaderFor(actualType);
...
reader.RegisterReference(referenceId, instance);
registered.Read(reader, instance);
```

出处：`Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:456-480`

$$
T_{\text{deserialize}} = O\!\left(V + E + \sum_{v} k_v^2 L\right)
$$

对于本库面向的视图模型图，成员数很小（个位数），所以二次项在实践中是小常数。只有成员达到几十个的类型才会显现。

```plot
{
  "title": "成员派发：名称链与哈希",
  "grid": true,
  "xAxis": { "domain": [0, 60] },
  "yAxis": { "domain": [0, 3600] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(k)，哈希派发" },
    { "fn": "x*x", "color": "#f472b6", "title": "O(k^2)，线性 if/else 链" }
  ]
}
```

## 注册表是快照

五张字典——写器、读取器、容器工厂、名称、反向名称——通过一个 volatile 快照一起发布。查找是一次 `TryGetValue`，无锁。注册是写时复制：替换一张表就复制它，所以一次注册花费 $O(W)$，进程生命周期内注册全部类型的总成本是 $O(W^2)$。模块初始化器注册每程序集在加载时发生一次，不是每文档。

## 封闭世界

没有反射回退。没有生成写器的类型会抛异常；没有生成读取器的成员类型也会抛异常，除非声明类型是 `object`——那时按文档形状读取。这正是本库裁剪与 AOT 安全的原因：类型闭包在编译期固定。

## 内存

写器持有引用字典，异步路径上还有一个 8 KB 字符缓冲，在 4 KB 处刷新。`Serialize()` 返回字符串，所以文档会短暂存在两份（写器与 `ToString` 副本）。读取器要么持有整个文档字符串 $O(D)$，要么持有增长到单个最大 token 的窗口缓冲 $O(B + \text{token})$；嵌套计数数组增长到 $O(\text{深度})$。两侧的引用表都是 $O(V)$。
