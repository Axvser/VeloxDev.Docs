# 权限模型

模型由六个类型组成：粗粒度模式、调用期分类、三态决定、按模式匹配的规则、被评判的调用，以及把它们组合起来的不可变策略。

## 枚举：AgentPermissionMode

智能体在必须询问之前能做多少，作为一个用户可切换的有名状态。

| 成员 | 值 | 含义 |
|---|---|---|
| `Plan` | `0` | 只读与提议。编辑、执行与策展一律拒绝。询问仍被允许。 |
| `Manual` | `1` | 每个非只读动作都先问用户。 |
| `AutoEdit` | `2` | 图编辑直接运行；执行与策展询问。 |
| `Auto` | `3` | 读取、编辑与执行直接运行；只有策展询问。默认值。 |
| `Bypass` | `4` | 不做任何询问。显式 `Deny` 规则仍然成立。 |

模式是**粗**层。规则位于其下，可以更严。宿主可随时切换模式；闸门每次调用读取模式，因此下一次调用由它评判。

## 枚举：AgentActionCategory

工具做什么，在调用即将运行时读取。

| 成员 | 值 | 含义 |
|---|---|---|
| `Read` | `0` | 仅检查；不能改变任何东西。 |
| `Edit` | `1` | 图变更：创建、删除、移动、连接、补丁、撤销/重做。 |
| `Execute` | `2` | 运行某物：节点代码、编译链、白名单命令、被派发的子智能体。 |
| `Curate` | `3` | 改变会话能触及的范围：添加、装载或重配 MCP 服务器。 |
| `Interact` | `4` | 询问机制本身——选择、确认、预算重置。从不会被模式拒绝。 |

`Curate` 是唯一其效果会超出对话的分类。把这一角色叠加到 `WorkflowToolCategory` 会把「是否发送」与「是否可运行」混为一谈。

## 枚举：PermissionDecision

| 成员 | 值 | 含义 |
|---|---|---|
| `Allow` | `0` | 不询问直接运行。 |
| `Ask` | `1` | 交给用户。没有注册处理器时，询问按拒绝处理。 |
| `Deny` | `2` | 不运行，也不提供。 |

## 记录：ToolInvocation

权限系统看到的一次调用。

```csharp
public sealed record ToolInvocation(
    string Name,
    AgentActionCategory Category,
    string? Source,
    IReadOnlyDictionary<string, object?> Arguments);
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 模型调用时使用的工具名。 |
| `Category` | `AgentActionCategory` | 工具做什么。 |
| `Source` | `string?` | 来源。MCP 服务器的工具带 `mcp:<server>`；MCP 管理 toolkit 带 `mcp:management`；其他工具为 `null`。 |
| `Arguments` | `IReadOnlyDictionary<string, object?>` | 模型提供、原样到达的参数。 |

参数存在是因为某些策略关乎调用**会做什么**：从本地包添加 MCP 服务器会安装软件，而 HTTP 端点只发送数据出去。

## 记录：AgentPermissionRule

```csharp
public sealed record AgentPermissionRule(PermissionDecision Decision, string Pattern);
```

规则按前缀命名的单一轴选择。

| 模式 | 匹配 |
|---|---|
| `DeleteNode`、`Get*`、`mcp:*` | 工具名，`*` 匹配任意字符序列。 |
| `category:Edit` | 一个 `AgentActionCategory` 中的全部工具。 |
| `source:mcp:*`、`source:mcp:filesystem`、`source:mcp:management` | 工具来源；只有 MCP 工具带来源。 |

匹配不区分大小写，没有转义。含 `*` 的名称无法精确匹配；工具名是 C# 标识符，因此没有代价。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Matches` | `bool Matches(ToolInvocation invocation)` | 规则是否针对此调用。为 null 时抛 `ArgumentNullException`。 |

## 类：AgentPermissionPolicy

会话的策略：一个模式、一个有序规则列表、一个仅在 `Auto` 使用的可选 judge。它不可变；每个 `With*` 返回新策略，因此一次求值持有前后一致的规则集。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Mode` | `AgentPermissionMode` | 生效的模式。 |
| `Rules` | `IReadOnlyList<AgentPermissionRule>` | 宿主规则，按加入顺序。 |
| `Judge` | `Func<ToolInvocation, PermissionDecision>?` | 在 `Auto` 中裁决规则与模式未决定的事项。 |
| `DefaultMode` | `static AgentPermissionMode` | `Auto`。图工作直接运行；询问移到改变会话可触及范围上。 |
| `For` | `static AgentPermissionPolicy For(AgentPermissionMode mode)` | 无规则、无 judge 的策略。 |
| `WithMode` | `AgentPermissionPolicy WithMode(AgentPermissionMode mode)` | 换一个模式的新策略。 |
| `WithRule` | `AgentPermissionPolicy WithRule(AgentPermissionRule rule)` | 添加一条规则；规则按决定求值，不按位置。 |
| `WithRules` | `AgentPermissionPolicy WithRules(IEnumerable<AgentPermissionRule> rules)` | 添加多条规则。 |
| `WithoutRules` | `AgentPermissionPolicy WithoutRules()` | 无规则策略；模式不变。 |
| `WithJudge` | `AgentPermissionPolicy WithJudge(Func<ToolInvocation, PermissionDecision>? judge)` | 设置或移除 judge。 |
| `Evaluate` | `PermissionDecision Evaluate(ToolInvocation invocation)` | 裁决一次调用。为 null 时抛 `ArgumentNullException`。 |
| `ModeDefault` | `static PermissionDecision ModeDefault(AgentPermissionMode mode, AgentActionCategory category)` | 没有规则与 judge 时模式给出的答案。 |

### 求值顺序

`Evaluate` 按权力从高到低，顺序就是契约：

1. `Deny` 规则——无条件，因此 `Bypass` 不是「安全系统关闭」；
2. `Plan` 的拒绝——同样无条件；规划期间 `Allow` 规则不能打开图编辑；
3. `Ask` 规则；
4. `Allow` 规则；
5. judge，仅 `Auto`；
6. `ModeDefault(mode, category)`。

judge 抛异常时答 `Deny`，绝不答 `Allow`。

### 模式矩阵

`ModeDefault` 是五种模式乘五个分类。

| 模式 | Read | Edit | Execute | Curate | Interact |
|---|---|---|---|---|---|
| `Plan` | Allow | Deny | Deny | Deny | Allow |
| `Manual` | Allow | Ask | Ask | Ask | Allow |
| `AutoEdit` | Allow | Allow | Ask | Ask | Allow |
| `Auto` | Allow | Allow | Allow | Ask | Allow |
| `Bypass` | Allow | Allow | Allow | Allow | Allow |

### 示例

```csharp
using VeloxDev.AI.Safety;

var policy = AgentPermissionPolicy.For(AgentPermissionMode.AutoEdit)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask, "DeleteNode"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"));

var call = new ToolInvocation(
    "DeleteNode", AgentActionCategory.Edit, null,
    new Dictionary<string, object?>());

Console.WriteLine(policy.Evaluate(call)); // Ask
```

## 相关

- [作用域安全](../01_作用域安全/index.md) —— 在 `WorkflowAgentScope` 上配置此策略。
- [预算与脏标记](../02_预算/index.md) —— 与权限并行的花费上限。
