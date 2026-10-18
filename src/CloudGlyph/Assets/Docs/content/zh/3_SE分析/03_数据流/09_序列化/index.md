# 数据流 — 序列化

归档路径分三段：**解析类型**、**选写者或读者**、**遍历成员**。运行期不发现任何东西 —— 注册表在程序集加载时由 `[ModuleInitializer]` 填好。

## 1. 写出文档

```plantuml
@startuml
!theme plain

actor "Caller" as C
participant "ViewModelSerializer" as VMS
participant "VeloxJsonSerializer" as VJS
participant "VeloxJsonWriter" as W
participant "VeloxJsonRegistry" as REG
participant "generated writer" as GW

C -> VMS: workflow.Serialize()
activate VMS
VMS -> VJS: Serialize(workflow, indented)
activate VJS
VJS -> W: new VeloxJsonWriter(output, indented)
activate W
VJS -> REG: WriterFor(runtimeType)
activate REG
REG --> VJS: IVeloxJsonWriter
deactivate REG

alt the type is not in the closed world
    VJS --> VMS: InvalidOperationException ("no registered JSON writer")
else the type is registered
    VJS -> GW: Write(writer, value, declaredType)
    activate GW
    GW -> W: WriteStartObject(instance, declaredType)
    GW -> W: one write per member, in declaration order
    GW -> W: WriteEndObject()
    GW --> VJS
    deactivate GW
end

VJS --> VMS: the document text
deactivate W
deactivate VJS
VMS --> C: json
deactivate VMS
@enduml
```

`WriteStartObject` 是格式身份所在：一个实例第一次出现时写出它的 id，并且**仅当运行期类型与声明类型不同时**写类型标签；第二次出现则写引用而不是对象（`Src/Core/VeloxDev.Core/Serialization/VeloxJsonWriter.cs:122-142`）。正是这一条分支让带 `Parent` 反向引用的图不会膨胀，也是为什么不存在 `PreserveReferencesHandling` 之类的设置。

## 2. 读取文档

```plantuml
@startuml
!theme plain

actor "Caller" as C
participant "ViewModelSerializer" as VMS
participant "VeloxJsonSerializer" as VJS
participant "VeloxJsonReader" as R
participant "VeloxJsonRegistry" as REG
participant "generated reader" as GR

C -> VMS: json.Deserialize<Inventory>()
activate VMS
VMS -> VJS: Deserialize<Inventory>(json)
activate VJS
VJS -> R: new VeloxJsonReader(json)
activate R
VJS -> R: BeginObject — read $id and optional $type
VJS -> REG: ReaderFor(type tag, or declaredType when none)
activate REG
REG --> VJS: IVeloxJsonReader
deactivate REG

alt no reader for the resolved type
    VJS --> VMS: InvalidOperationException ("no registered JSON reader")
else a reader exists
    VJS -> GR: Create()
    activate GR
    GR --> VJS: a fresh instance, parameterless constructor already run
    deactivate GR
    VJS -> GR: Read(reader, target)
    activate GR
    GR -> R: NextMember / MemberNameEquals, then a typed read per member
    GR --> VJS
    deactivate GR
end

VJS --> VMS: the rebuilt object
deactivate R
deactivate VJS
VMS --> C: Inventory
deactivate VMS
@enduml
```

读侧有三条性质：

- **文档的成员顺序无关紧要。** `NextMember()` 前进，`MemberNameEquals(name)` 就地比较；读者只索取自己认识的成员，其余跳过。这也解释了为什么文档里没有的成员会保持构造函数留下的值 —— 不存在「恢复默认值」这一遍。
- **构造函数先运行，成员随后写到实例上。** 构造函数设置过、而文档没有提到的内容会活过加载。
- **类型标签走同一张注册表。** `TypeOf(name) ?? declaredType` —— 退回声明类型时，具体类会静默丢失多态，接口或抽象类型则抛出由 `MissingReader` 构造的 `InvalidOperationException`（`VeloxJsonSerializer.cs:453-463`）。

## 3. 两条链路在哪里分叉

读与写各自存在**两份** —— 一条同步链路、一条异步链路 —— 而且它们是两条手写路径，不是一条路径加 `await`。原因是内存内路径从不做 I/O，在那里为异步状态机付费纯属浪费。

代价是两者必须一致，而结构上没有任何东西强制它们一致：`ShapeRoundTripTests.TheTwoChains_SpellEveryScalarTheSameWay` 与 `ElementScalarRoundTripTests` 把标量拼写和运行期类型元素钉在一起。生成器为每个类型同时产出两半（`IVeloxJsonWriter` / `IVeloxJsonReader` 各声明同步与异步方法），所以类型不会只被支持一半。
