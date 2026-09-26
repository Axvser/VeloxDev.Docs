# 工作流代理 — 子代理：工具包与上下文提供器

把子系统送到模型面前的是两个公开类型：`SubAgentAgentToolkit` 是子系统的面向 Agent 视图（五个工具），`SubAgentAgentContextProvider` 是这些工具 —— 连同解释它们的那些文字 —— 到达一次 agent 调用的路径。两者都位于 `VeloxDev.AI.SubAgents`，实现在 `Agent/SubAgents/`。

## 类：`SubAgentAgentToolkit`

`public sealed class SubAgentAgentToolkit(SubAgentScope scope, WorkflowAgentScope host)` —— 主构造器类；两个参数都在字段初始化器里做空检查，所以传入 null 会在构造时抛 `ArgumentNullException`。

| 成员 | 签名 | 备注 |
|---|---|---|
| `ToolNames` | `static readonly string[]` | `["SpawnSubAgent", "WaitSubAgents", "GetSubAgentResult", "ListSubAgents", "CancelSubAgent"]`。公开它，是为了让组合多个工具源的宿主不必重复字面量就能对它们分类；五个相对工作流图都是**只读**的，所以工作流工具包不会把它们算进变更预算，也不会因它们标脏。 |
| `CreateAllTools` | `IList<AITool> CreateAllTools()` | 本工具包能提供的全部工具，**忽略宿主的开关**。宿主 UI 枚举它来展示可切换的面。 |
| `CreateTools` | `IList<AITool> CreateTools()` | 同一集合，未包装，省略被宿主关掉的工具（`host.IsToolEnabled`）。 |
| `CreateTools` | `IList<AITool> CreateTools(ToolPipeline tools, AgentPipeline? pipeline = null)` | 用 `TrackedAIFunction` 包装，于是每次调用都被编组到宿主的线程上、与其他调用受同一份预算门禁、并在事后上报。`tools` 为 null 时抛 `ArgumentNullException`。**上下文提供器贡献的就是这一份。** |

### 五个工具

五个工具在形状上都是异步的，即便某些工作本身是即时的。这是**契约**而不是实现细节：`SpawnSubAgent` 返回句柄并在后台跑孩子，所以调用方从不在一次工具调用内部等孩子，而读 schema 的宿主看到的是「派发后轮询」而不是「调用即阻塞」。

| 工具 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `SpawnSubAgent` | `task` | `name`、`allowedTools`、`allowedSkills`、`allowedMcpServers`、`maxToolCalls`、`maxReadToolCalls`、`maxWriteToolCalls`、`allowNodeExecution`、`allowedGenericCommands`、`autoMarkDirty`、`notes` | `{status, id, name, depth, maxToolCalls, grantedToolCount, grantedSkillCount, grantedMcpServerCount, dropped[], message}` |
| `WaitSubAgents` | — | `ids`、`timeoutMs`（默认 60000） | `{status, timedOut, agents[], message}` |
| `GetSubAgentResult` | `id` | — | `{status, id, name, depth, state, stateText, callCount, maxToolCalls, grantedToolCount, grantedSkillCount, grantedMcpServerCount, dropped[]?, result?, error?}` |
| `ListSubAgents` | — | — | `{status, count, running, agents[]}`（每项：`id, name, depth, state, stateText, callCount, task`） |
| `CancelSubAgent` | `id` | — | 与 `GetSubAgentResult` 同形状 |

失败一律是 JSON 对象，绝不是异常：被拒的 spawn 或未知句柄返回 `{"status":"refused","message":"…"}`。`SpawnSubAgent` 还会在**什么都没创建之前**拒绝空 `task` —— `SubAgentNarrowingTests.ASpawnWithNoTask_IsRefusedBeforeAnythingIsCreated` 断言不留下任何行。

各工具的载荷细节：

- `SpawnSubAgent` 的 `dropped` 是「这次 spawn 要了却没拿到」的逐行清单；非空时 `message` 改为「Dispatched, but not with everything you asked for — read "dropped"」。
- `WaitSubAgents` 把每份汇报截断到 4000 字符，截断标记既写在**正文里**也写在 `truncated` 字段里，所以只读正文的模型也能分辨完整汇报与被切过的汇报。`GetSubAgentResult` 给出未截断的完整汇报。*推断所得* —— 载荷形状是被断言过的（`SubAgentDispatchTests.ASecondWait_CollectsWhatTheFirstTimedOutOn` 把 `result` 原样读回），但 4000 这个上限本身是读源码得到的，没有测试覆盖它。
- `ListSubAgents` 把任务预览截断到 120 字符；名册提示词那一行截断到 100 字符。*推断所得* —— 读源码所得；没有测试用过一个长到会被切的任务。

`SubAgentToolSchemaTests` 钉住模型实际读到的 schema：`SpawnSubAgent` 的**唯一**必填参数是 `task`；十二个能力参数全部有描述；`WaitSubAgents` 与 `ListSubAgents` 无必填；`GetSubAgentResult` 与 `CancelSubAgent` 恰好必填 `id`。

## 类：`SubAgentAgentContextProvider`

`public sealed class SubAgentAgentContextProvider : AIContextProvider` —— 向一次 agent 调用贡献常驻文字、名册，以及包装好的五个工具。

| 成员 | 签名 | 备注 |
|---|---|---|
| `SubAgentAgentContextProvider` | `SubAgentAgentContextProvider(SubAgentScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | `scope` 为 null 时抛 `ArgumentNullException`。独立使用时省略 `tools`：会从 `scope.Parent?.UIContext` 推导出一份只管线程的策略。 |
| `StateKeys` | `override IReadOnlyList<string> { get; }` | 每个子系统实例恰好一个键：`"{nameof(SubAgentAgentContextProvider)}:{scope.InstanceId}"`。 |

`ProvideAIContextAsync` 按作用域的 `Version` 渲染，所以一个孩子完成会在下一轮就到达模型，而不必重建 agent：被缓存的是**渲染结果**，而不是发送行为 —— 指令每次调用都是临时的，工具是随版本缓存的实例，两者每次都照常交回。

这里**没有语言维度**。本子系统自己的文字一次性写成双语（标题形如 `## 子代理 / Sub-agents`），不跟随工作流提示词语言，因为子代理的简报是给模型读的，不是给用户读的。

## 提示词的两半

`BuildInstructions` 拼接两次渲染，各回答一个不同的问题：

- `BuildPromptContext()` —— **常驻文字**，宿主与孩子都读。它按宿主实际提供的工具（`CreateTools()`）构建，所以被关掉的工具不会被广告；宿主一个都不提供时它是**空的**。其中承载语义的句子被 `SubAgentDispatchTests` 按字符串钉住：
  - 强制委派的判据是关于**工作的种类**的规则（`must be dispatched to a sub-agent`），而不是一句许可；例外句刻意收窄（`only when the entire answer is one value read off a single call`），旧的、更宽的措辞被**反向断言**其不再出现；
  - 标题是在模型每轮都读的地方被要求的（`Title each one with \`name\``），而不只在参数描述里；
  - spawn 交下去什么，写在模型读得到的地方（`omit them to hand down the lot`）；
  - 「它问不到**你**」—— 它仍可能直接把问题交给用户，因为孩子继承了宿主的交互配置。
- `BuildRosterBlock()` —— **动态块**：给孩子看的 `ChildBriefing`（深度、额度、notes、被拒请求、被收窄时列出被授予的技能/服务器、以及它还能不能派发），随后是模型自己孩子的名册。名册只在有了孩子之后才出现（`SubAgentDispatchTests.TheRoster_OnlyAppearsOnceThereAreChildren`）。

`ChildBriefing` 之所以存在，是因为孩子的 **instructions 是宿主的**：`ForClient` 写一份固定前言，宿主自定义一份就会丢掉这次 spawn 的全部事实。改由每轮在孩子自己的名册旁补，两种选择下都成立 —— `SubAgentHierarchyTests.AChildIsToldWhatItIs_AndWhatItDidNotGet`。

名册同时也是孩子能否派发的措辞闸门：`AppendBriefing` 在深度到顶时说「你不能派发 —— 自己做」，否则肯定地说孩子**可以**派发；后者由 `MayDispatch`（`host.IsToolEnabled("SpawnSubAgent")`，与 `CreateTools()` 过滤用的同一个开关）守卫，所以两者不可能互相矛盾。`AChildThatCannotDispatch_IsNotToldItCan` 与 `AChildDispatchedWithoutAWhitelist_IsToldItMayDispatchToo` 各钉一半。

> 源码：`SubAgentAgentToolkit.cs` 第 31-76 行（工具包）、238-374 行（提示词构建）；`SubAgentAgentContextProvider.cs` 第 24-113 行。测试：`Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/` 下的 `SubAgentToolSchemaTests`、`SubAgentDispatchTests`（提示词钉子）、`SubAgentHierarchyTests`（简报钉子）。
