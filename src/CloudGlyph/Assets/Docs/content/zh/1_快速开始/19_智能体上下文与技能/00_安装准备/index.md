# 安装准备

## 前置条件

- **支持的目标框架：** `netstandard2.0` 与 `net8.0`，见 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。
- **SDK：** .NET SDK 8.0 或更新；测试运行在 .NET 10。
- **包：** `VeloxDev.Core.Extension` 12.3.0。
- **生成器（给自己的类型加 `[AgentContext]` 时需要）：** 以分析器方式引用 `VeloxDev.Core.Generator` 12.3.0。内置工作流技能不依赖它。
- **渲染上下文或枚举技能不需要模型。**

## 安装

```powershell
dotnet new console -n AgentContextQuickStart
cd AgentContextQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**预期结果：** `dotnet list package` 中能看到 `VeloxDev.Core.Extension`。

## 创建 scope

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithOutputLanguage(AgentLanguages.Chinese)
    .WithAutoDiscovery();

Console.WriteLine(scope.PromptLanguage); // English
```

`WithAutoDiscovery()` 读取生成器编译进被引用程序集的代理上下文树。`WithPromptLanguage` 选择指令文本的语言，`WithOutputLanguage` 选择模型回答的语言。

**预期结果：** 输出 `English`。不需要聊天客户端，scope 已经可以渲染上下文。

## 用声明式描述一个类型

`AgentContextAttribute` 给类型或成员附上一段自然语言描述。它可以重复标注，每种语言一条。

```csharp
using VeloxDev.AI;

[AgentContext(AgentLanguages.English, "A node that runs a Python script and exposes one output slot per declared port.")]
[AgentContext(AgentLanguages.Chinese, "运行 Python 脚本的节点，按声明的端口各暴露一个输出槽。")]
public sealed class ScriptNodeViewModel
{
    public string Script { get; set; } = string.Empty;
}
```

**预期结果：** 生成器运行后，`AgentContextCollector.GetClassContext(typeof(ScriptNodeViewModel), AgentLanguages.English)` 返回包含那句英文的 Markdown 块。

## 手动注册类型

自动发现不是唯一途径。宿主可以点名它需要的类型：

```csharp
scope.WithComponents(new[] { typeof(ScriptNodeViewModel) }, AgentLanguages.English)
     .WithEnums(new[] { typeof(SlotState) }, AgentLanguages.English)
     .WithInterfaces(new[] { typeof(INodeComponent) }, AgentLanguages.English)
     .WithData(new[] { typeof(Anchor) }, AgentLanguages.English);
```

| 方法 | 渲染内容 |
|---|---|
| `WithComponents` | 命令、槽、提升属性 |
| `WithEnums` | 枚举成员及其含义 |
| `WithInterfaces` | 接口约定 |
| `WithData` | 值对象的属性与标注字段 |

**预期结果：** `scope.ProvideCustomerContext()` 现在包含框架的枚举、接口与数据块。组件块要等生成器为 `ScriptNodeViewModel` 编译出上下文条目后才会出现。

## 选择提示词形态

```csharp
var progressive = scope.ProvideProgressiveContextPrompt(); // 静态骨架
var full        = scope.ProvideAllContexts();              // 骨架加全部上下文，一次给出
var framework   = scope.ProvideFrameworkContext();         // 仅框架类型
var customer    = scope.ProvideCustomerContext();          // 仅宿主注册的类型
```

**预期结果：** `progressive` 远短于 `full`，并且默认树下 `framework` 非空。
