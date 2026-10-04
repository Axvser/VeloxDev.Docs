# 函数 · 辅助类

三个静态辅助类支撑命令、补丁与 schema 工具。

## CommandInvoker

`public static class CommandInvoker` —— 发现并调用 workflow 组件上的 `IVeloxCommand` 属性；支撑 `ListComponentCommands`、`ExecuteCommandOnNode`、`ExecuteCommandById`。把 JSON 参数反序列化为 `[AgentCommandParameter]` 声明的类型。

| 成员 | 签名 | 说明 |
|---|---|---|
| `DiscoverCommands` | `IReadOnlyList<CommandDescriptor> DiscoverCommands(object component)` | `ICommand` 类型属性 —— 先接口属性（权威特性），再具体类型自身的（去重）。 |
| `Invoke` | `string Invoke(object component, string commandName, string? jsonParameter)` | 执行命名命令，返回 JSON；缺 `"Command"` 后缀会自动补。命令缺失或命令属性为 null 时返回 `status:"error"` JSON，而非异常。 |

`CommandDescriptor`（`public class`）声明于同一文件：`Name`（`string`）、`ParameterType`（`Type?`，来自 `[AgentCommandParameter]`）、`Descriptions`（`IReadOnlyList<KeyValuePair<AgentLanguages, string>>`）。

## ComponentPatcher

`public static class ComponentPatcher` —— 通过设置可写公开属性把 JSON 补丁对象应用到组件。支撑 `PatchNodeProperties` / `PatchComponentById`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ApplyPatch` | `string ApplyPatch(object target, string jsonPatch)` | 应用 `{"Prop": value}`。拒绝（带 `rejected`/`skipped` + `reason`）框架管理的属性（`Parent`、`Nodes`、`Links`、`LinksMap`、`Slots`、`Targets`、`Sources`、`State`、`VirtualLink`、`RuntimeId`、`Helper`）、命令驱动的属性（路由到其后备命令）、槽类型与带 `[SlotSelectors]` 的属性；对未挂载到树上的目标报错；`Type` 属性经 `TypeIntrospector` 解析类型名。直接写入刻意不可撤销。 |
| `ApplyPatchWithUndo` | `string ApplyPatchWithUndo(object target, string jsonPatch, IWorkflowTreeViewModel? tree = null)` | 向后兼容别名 → `ApplyPatch`（`tree` 被忽略）。 |
| `CopyScalarProperties` | `void CopyScalarProperties(object source, object target)` | 复制可写标量/枚举属性，跳过命令/槽/框架管理的属性。 |

## TypeIntrospector

`public static class TypeIntrospector` —— 类型解析 + 供 Agent 消费的 JSON schema；支撑 `GetTypeSchema`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `ResolveType` | `Type? ResolveType(string fullTypeName)` | 委托给 Core 的 `AgentTypeResolver.ResolveType`。 |
| `GetTypeSchema` | `string GetTypeSchema(Type type)` | 缩进 JSON：`fullName`、`kind`（enum/interface/struct/class）、`baseType`、`interfaces`、枚举 `values` 或属性列表（`name`/`type`/`canRead`/`canWrite`），外加开发者指令。 |

## 示例

```text
// Source: Test
CommandInvoker.DiscoverCommands(node)                 → [{Name:"ReceiveCommand", ParameterType:null, ...}]
CommandInvoker.Invoke(node, "ReceiveCommand", null)   → {"status":"ok","message":"Command 'ReceiveCommand' executed."}
CommandInvoker.Invoke(node, "NoSuchCommand", null)    → {"status":"error","message":"Command 'NoSuchCommandCommand' not found on type '...'."}
TypeIntrospector.ResolveType("System.String")         → typeof(string)
```

**预期结果：** 未知命令名被规范为 `NoSuchCommandCommand` 并以错误报告，绝不抛出。
