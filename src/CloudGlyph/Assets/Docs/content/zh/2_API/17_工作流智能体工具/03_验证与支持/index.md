# 验证与支持

这些类型支撑 `ValidateWorkflow`、`ExecuteCommandOnNode`、`PatchNodeProperties` 与 `GetTypeSchema` 工具。它们可以直接使用，但多数宿主只注册一个领域验证器，其余交给 toolkit。

## 接口：IWorkflowTreeValidator

`VeloxDev.AI.Workflow.IWorkflowTreeValidator` 是宿主或插件注册的领域验证器，使 `ValidateWorkflow` 能报告结构检查看不到的问题。toolkit 负责结构检查（零尺寸节点、重复连线、环）；组件库知道自己的必填字段，就加在这里。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Name` | `string Name { get; }` | 报告在此验证器产生的每条问题旁的名字。 |
| `Validate` | `IEnumerable<WorkflowValidationIssue> Validate(ITreeComponent tree)` | 返回发现的问题。空序列表示领域检查通过。树是实时的，不得修改。 |

实现必须只读。注册表在每次 `ValidateWorkflow` 调用时读取一次，因此服务器启动后注册的验证器会在下次调用生效。

## 记录：WorkflowValidationIssue

```csharp
public sealed record WorkflowValidationIssue(
    string Level,
    int NodeIndex,
    string? ComponentId,
    string Message,
    string? Code = null);
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `Level` | `string` | 严重度：`error`、`warn` 或 `info`。 |
| `NodeIndex` | `int` | 问题所属节点；树级问题为 `-1`。 |
| `ComponentId` | `string?` | 组件的运行时 id，当问题属于某个组件时。 |
| `Message` | `string` | 人类可读的描述。 |
| `Code` | `string?` | 宿主可匹配的可选稳定代码。 |

## 类：WorkflowValidation

`VeloxDev.AI.Workflow` 中进程级验证器注册表。

| 方法 | 返回 | 说明 |
|---|---|---|
| `Register(IWorkflowTreeValidator validator)` | `void` | 添加验证器；重复注册同一实例是无操作。为 null 时抛 `ArgumentNullException`。 |
| `Unregister(IWorkflowTreeValidator validator)` | `bool` | 移除验证器；曾注册时为 `true`。 |
| `Snapshot()` | `IReadOnlyList<IWorkflowTreeValidator>` | 已注册验证器的稳定副本。 |
| `Clear()` | `void` | 移除全部验证器，供宿主与测试在会话之间使用。 |

注册通常在程序集的模块初始化器中完成，因此加载程序集就是让其验证可用。

```csharp
using VeloxDev.AI.Workflow;

WorkflowValidation.Register(new MyDomainValidator());
var issues = new MyDomainValidator().Validate(tree);
```

## 类：CommandInvoker

`VeloxDev.AI.Workflow.Functions.CommandInvoker` 通过组件的编译上下文树条目发现并调用其命令属性。`ListComponentCommands` 与 `ExecuteCommandOnNode` 调用的就是它。

| 方法 | 返回 | 说明 |
|---|---|---|
| `DiscoverCommands(object component)` | `IReadOnlyList<CommandDescriptor>` | 树记录的、含继承的命令属性；组件为 null 或类型不在树中时为空。 |
| `Invoke(object component, string commandName, string? jsonParameter)` | `string` | 调用命名命令，把 JSON 参数反序列化为 `[AgentCommandParameter]` 声明的类型。缺少 `Command` 后缀时补上。返回 JSON 状态对象。 |

`Invoke` 不查询命令的 `CanExecute`；报告无法运行的命令仍会被运行。

## 类：CommandDescriptor

组件向智能体暴露的一条命令属性。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Name` | `string` | 命令属性名。 |
| `ParameterType` | `Type?` | `[AgentCommandParameter]` 声明的类型；命令无参数时为 `null`。 |
| `Descriptions` | `IReadOnlyList<KeyValuePair<AgentLanguages, string>>` | 命令的描述，各带其语言。 |

## 类：ComponentPatcher

`VeloxDev.AI.Workflow.Functions.ComponentPatcher` 通过设置可写公共属性把 JSON 补丁对象应用到组件。由命令支撑的属性（如 `Anchor` → `SetAnchorCommand`）会被拒绝，因此不会绕过命令管线。

| 方法 | 返回 | 说明 |
|---|---|---|
| `ApplyPatch(object target, string jsonPatch)` | `string` | 应用 `{"Title":"New","Delay":500}` 形式的补丁。返回描述成功与失败的 JSON 结果。 |
| `ApplyPatchWithUndo(object target, string jsonPatch, ITreeComponent? tree = null)` | `string` | 向后兼容别名；树参数被忽略，从目标父链解析。 |
| `CopyScalarProperties(object source, object target)` | `void` | 在两个同类型对象之间复制可写、非命令、非 `ICommand` 的属性。 |

## 类：TypeIntrospector

`VeloxDev.AI.Workflow.Functions.TypeIntrospector` 把智能体上下文树承载的类型描述成模型可读的 JSON。一切都来自编译上下文树，不使用反射。

| 方法 | 返回 | 说明 |
|---|---|---|
| `ResolveType(string fullTypeName)` | `Type?` | 从上下文树按全名解析类型；树中没有时为 `null`。 |
| `GetTypeSchema(Type type)` | `string` | 缩进的 JSON schema 式描述：成员、基类型、接口与枚举值。 |

schema 是描述而非契约。`defaultJson` 是零初始化实例而非作者意图的默认值，因此调用方应信任 `developerInstructions` 字段。

## 相关

- [WorkflowAgentToolkit](../01_工作流工具集/index.md) —— 调用这些辅助工具的工具。
- [WorkflowAgentScope](../00_工作流作用域/index.md) —— 持有被检查树的作用域。
