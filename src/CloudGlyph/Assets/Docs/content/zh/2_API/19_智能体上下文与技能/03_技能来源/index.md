# 技能来源

来源是让 `SkillScope` 统一对待嵌入提示文档与磁盘 Agent Skills 文件夹的接缝。发现从不产生技能正文；那是 `ReadBody` 的职责，使大型技能在模型索取前不产生成本。

## 接口：ISkillSource

| 成员 | 签名 | 说明 |
|---|---|---|
| `Kind` | `SkillSourceKind Kind { get; }` | 这是哪个加载器；决定技能的注入模式。 |
| `Discover` | `IReadOnlyList<SkillDescriptor> Discover()` | 枚举此来源可提供的技能。文本存在于多种语言时可能多次产出同一名称。 |
| `ReadBody` | `string? ReadBody(string skillName, AgentLanguages language)` | 读取指定语言的技能全文；不可用时为 `null`。 |
| `ReadResource` | `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` | 读取一个随附资源，相对于技能目录寻址。 |

发现无副作用。文件技能的 `SKILL.md` 会完整读取，因为否则无法解析 frontmatter；但随附资源只被枚举，从不打开。

## 类：EmbeddedSkillSource

发现程序集中 `Resources/{System}/{lang}/Skills/{Name}.md` 下嵌入的提示文档。名称优先取 YAML frontmatter，否则取文件名。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `EmbeddedSkillSource(string system)` | 为某个系统的嵌入技能创建来源，如 `"Workflow"`。 |
| `Kind` | `SkillSourceKind` | 恒为 `Embedded`。 |
| `Discover` | `IReadOnlyList<SkillDescriptor> Discover()` | 每个（名称，语言）一个描述，因为同一技能通常每种支持语言各一份。 |
| `ReadBody` | `string? ReadBody(string skillName, AgentLanguages language)` | 读取嵌入正文。 |
| `ReadResource` | `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` | 恒返回 `null`：嵌入技能无逐技能资源；共享 References 语料另有注入路径。 |

## 类：FileSkillSource

按 Agent Skills 约定以 `<root>/<name>/SKILL.md` 从磁盘发现技能。`SKILL.md` 旁的 `references/` 树携带额外文档，发现时计数、按需读取。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `FileSkillSource(string rootPath)` | 为某个根创建来源。发现延迟到 `Discover`；目录可以尚不存在。 |
| `Kind` | `SkillSourceKind` | 恒为 `File`。 |
| `Root` | `string` | 解析后的根目录。 |
| `Discover` | `IReadOnlyList<SkillDescriptor> Discover()` | 查找技能文件夹（或根下直接的一个 `SKILL.md`）。 |
| `ReadBody` | `string? ReadBody(string skillName, AgentLanguages language)` | 读取 frontmatter 之下的 `SKILL.md`。 |
| `ReadResource` | `string? ReadResource(string skillName, string relativePath, AgentLanguages language)` | 读取技能 `references/` 树下的一个文件。 |

文件技能语言中立，因此 `language` 参数为接口一致性而接受并被忽略。

## 相关

- [技能作用域](../01_技能作用域/index.md) —— 消费这些来源。
- [技能状态](../02_技能状态/index.md) —— 来源产出的描述。
