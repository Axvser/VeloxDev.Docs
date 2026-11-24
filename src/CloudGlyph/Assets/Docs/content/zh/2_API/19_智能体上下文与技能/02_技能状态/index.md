# 技能状态

`VeloxDev.AI.Skills` 提供已发现技能的三种相关视图：每个技能一个可绑定行、一个可在 UI 线程外安全读取的不可变摘要，以及 `SkillScope.Status` 持有的聚合集合。`SkillDescriptor` 是它们背后的发现期记录。

## 类：SkillStatusViewModel

一个技能作为可绑定行，遵循框架的 `[VeloxProperty]` 约定。`IsEnabled` 刻意独立于 `State`：技能可以可读却被关闭，而关闭不得卸载它。

### 生成属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 技能名。 |
| `Description` | `string` | 用于匹配请求的一行描述。 |
| `State` | `SkillState` | 生命周期状态。 |
| `Source` | `SkillSourceKind` | 由哪个加载器产生。 |
| `Path` | `string?` | 嵌入资源名或文件路径；仅用于报告。 |
| `IsEnabled` | `bool` | 技能能否贡献到提示。默认 `true`。 |
| `ResourceCount` | `int` | 随附资源文件数。 |
| `Error` | `string?` | 技能不可用的原因，或 `null`。 |

### 计算成员

| 名称 | 类型 | 说明 |
|---|---|---|
| `IsReady` | `bool` | `State == Ready`。 |
| `IsError` | `bool` | `State == Error`。 |
| `IsActive` | `bool` | `IsReady && IsEnabled`——它贡献到提示。 |
| `HasResources` | `bool` | `ResourceCount > 0`。 |
| `ResourceNames` | `IReadOnlyList<string>` | 随附资源路径，相对技能目录、以 `/` 分隔——正是 `read_skill_resource` 接受的字符串。 |
| `StateText` | `string` | 状态的展示文本。 |

## 类：SkillSummary

一个技能身份与开关状态的不可变副本，可从任意线程读取。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 技能名。 |
| `Description` | `string` | 一行描述。 |
| `Source` | `SkillSourceKind` | 由哪个加载器产生。 |
| `IsActive` | `bool` | 可读且已打开。 |

## 类：SkillsViewModel

`SkillScope.Status` 持有的全局可绑定技能视图模型。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Skills` | `ObservableCollection<SkillStatusViewModel>` | 可绑定行，由被跟踪集合生成。 |
| `Snapshot` | `IReadOnlyList<SkillSummary>` | 不可变副本，在被跟踪技能变化时于绑定线程重新发布。在其他线程读它。 |
| `ActiveCount` | `int` | 可读且已打开的技能数。 |
| `ErrorCount` | `int` | 加载失败的技能数。 |
| `HasError` | `bool` | 是否至少一个技能失败。 |
| `Track` | `void Track(SkillStatusViewModel skill)` | 注册技能并订阅其变化，使聚合刷新。 |
| `Reset` | `void Reset()` | 移除所有被跟踪技能。 |

智能体调用在框架选择的线程上渲染提示，因此在那里枚举 `Skills` 会与宿主 UI 竞争。绑定线程之外使用 `Snapshot`。

## 类：SkillDescriptor

来源在读取正文前知道的技能信息。一个来源可能为同一名称产生多个描述——每种语言一个——因为技能作为一个概念开关，而其文本按提示语言渲染。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 技能名。文件技能必须与父目录名一致。 |
| `Description` | `string` | 一行描述。 |
| `Source` | `SkillSourceKind` | 由哪个加载器产生。 |
| `Path` | `string?` | 文件路径或嵌入资源名；仅报告。 |
| `Language` | `AgentLanguages?` | 文本语言；语言中立的文件技能为 `null`。 |
| `ResourceCount` | `int` | 随附资源文件数，发现时计数但不打开。 |
| `ResourceNames` | `IReadOnlyList<string>` | 相对资源路径，以 `/` 分隔——`read_skill_resource` 接受的形式。 |
| `Error` | `string?` | 技能不可用的原因，或 `null`。格式错误的技能会被报告，不抛出也不丢弃。 |

## 相关

- [技能作用域](../01_技能作用域/index.md) —— 发现与开关。
- [技能来源](../03_技能来源/index.md) —— 描述来自哪里。
