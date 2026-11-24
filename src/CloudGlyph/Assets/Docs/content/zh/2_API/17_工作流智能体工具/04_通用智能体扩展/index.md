# 通用智能体扩展

这些 `VeloxDev.AI` 辅助工具在工作流层之外同样适用。它们与工作流作用域使用同一批 provider、策略与管线组合。

## 类：AgentClientExtensions

| 成员 | 签名 | 说明 |
|---|---|---|
| `AsAIAgent` | `static ChatClientAgent AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` | 创建一个智能体，其说明为给定静态骨架，工具完全来自 `providers`。刻意没有 tools 参数：框架会把 provider 工具与 `ChatOptions.Tools` 做并集且不去重，去掉参数就让这个错误无从发生。 |

```csharp
var agent = chatClient.AsAIAgent([mcp.CreateContextProvider()]);
```

## 类：AgentObjectToolkit

`VeloxDev.AI.AgentObjectToolkit : IAgentToolCallNotifier` 使用编译上下文树、生成的访问器、`TypeIntrospector` 与 `ComponentPatcher`，把任意 .NET 对象包装成 MAF 兼容工具。它是 `WorkflowAgentToolkit` 的通用、非工作流对应物。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `AgentObjectToolkit(object target, AgentLanguages language = AgentLanguages.English, ISet<string>? rejectedProperties = null)` | 暴露 `target`；`rejectedProperties` 指定补丁工具必须拒绝的属性。 |
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>?` | 每次成功调用后触发。拒绝与失败经 `Pipeline` 上的 `AgentToolCallCompleted` 传递。 |
| `MaxToolCalls` | `int?` | 调用上限；`null` 表示不限。 |
| `CreateTools()` | `IList<AITool> CreateTools()` | 创建所有通用工具，已包装，使 `ToolCalled` 触发且管线上报。 |
| `Pipeline` | `AgentPipeline` | toolkit 的事件链，首次使用时创建。 |
| `Tools` | `ToolPipeline` | 交给每个包装器的工具接缝：一个调用上限与一个上报点。按设计不注册线程编组，因为被包装目标是任意对象而非 UI 绑定组件。 |

生成器未纳入的类型仍获得十个工具，但每个都回答该类型不在树中。这个封闭世界正是工具面可裁剪的原因。

## 类：AgentObjectToolkitExtensions

| 成员 | 签名 | 说明 |
|---|---|---|
| `AsAgentToolkit` | `static AgentObjectToolkit AsAgentToolkit(this object target, AgentLanguages language = AgentLanguages.English, ISet<string>? rejectedProperties = null)` | 在任意对象上创建 toolkit。 |
| `AsAgentTools` | `static IList<AITool> AsAgentTools(this object target, AgentLanguages language = AgentLanguages.English, ISet<string>? rejectedProperties = null)` | 便捷方法：创建 toolkit 并返回所有工具。 |

## 类：AgentTelemetryExtensions

打开 Agent Framework 自身的 OpenTelemetry 插桩。库自身不发出遥测；`AgentTranscript` 与 `AgentPipeline` 是面向宿主的表面，二者都不离开进程。

| 成员 | 签名 | 说明 |
|---|---|---|
| `UseAgentTelemetry` | `static AIAgentBuilder UseAgentTelemetry(this AIAgentBuilder builder, string? sourceName = null, bool enableSensitiveData = false)` | 插桩该 builder 构建的每次运行。优先于包装成品智能体；source 名还须在宿主的 `TracerProvider` / `MeterProvider` 注册。 |
| `WithAgentTelemetry` | `static AIAgent WithAgentTelemetry(this AIAgent agent, string? sourceName = null, bool enableSensitiveData = false)` | 直接插桩，供未使用 builder 的调用方。 |

`enableSensitiveData` 默认 `false`，开发之外应保持：打开后 span 携带完整对话文本，包括工具结果。

## 相关

- [WorkflowAgentScope](../00_工作流作用域/index.md) —— 这些辅助工具的工作流对应物。
- [智能体仪表盘与转录](../../22_智能体仪表盘与转录/01_事件管线/index.md) —— 库自己的观察表面。
