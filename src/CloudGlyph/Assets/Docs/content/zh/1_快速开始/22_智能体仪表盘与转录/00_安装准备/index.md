# 安装准备

## 前置条件

- **支持的目标框架：** `netstandard2.0` 与 `net8.0`，见 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。
- **SDK：** .NET SDK 8.0 或更新；测试运行在 .NET 10。
- **包：** `VeloxDev.Core.Extension` 12.3.0。
- **构建转录或仪表盘不需要模型。** 媒体输入需要接受该媒体类型的模型。

## 安装

```powershell
dotnet new console -n AgentDashboardQuickStart
cd AgentDashboardQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**预期结果：** `dotnet list package` 中能看到 `VeloxDev.Core.Extension`。

## 创建转录

```csharp
using VeloxDev.AI.Pipelines;

var transcript = new AgentTranscript();

transcript.AddUser("列出节点。");
transcript.AppendReasoning("应该先调用 ListNodes。");
transcript.AddToolCall("ListNodes", """{"status":"ok","nodes":[]}""", AgentToolOutcome.Succeeded);
transcript.AppendAnswer("图里没有节点。");

Console.WriteLine(transcript.Entries.Count); // 4
```

`AddUser` 与 `AddToolCall` 会关闭任何打开的答案。`AppendAnswer` 与 `AppendReasoning` 延续同角色的打开条目；遇到工具调用后会在新条目里续写，而不是丢字。

**预期结果：** 四个条目；答案是一个 `Assistant` 条目，思考是一个 `Reasoning` 条目。

## 接到 scope

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithTranscript(transcript);

var pipeline = scope.Pipeline;
```

`WithTranscript` 组装管线对 `RunAsync` 与 `RunStreamingAsync` 都使用的阶段链。要在构建智能体**之前**挂上：智能体会被这条链包住，宿主因此不必自己循环流。

**预期结果：** `scope.Transcript` 与 `transcript` 是同一实例。

## 创建仪表盘

```csharp
using VeloxDev.AI.Dashboard;

var dashboard = AgentDashboardViewModel.Create(scope);
Console.WriteLine(dashboard.SystemToolSummary); // 启用/提供
Console.WriteLine(dashboard.SkillSummary);      // 开启/发现
Console.WriteLine(dashboard.McpSummary);        // 已连接/已配置
Console.WriteLine(dashboard.SubAgentSummary);   // 运行中/已派发
```

`Create` 直接读取 scope，所以 scope 不必先配置好。之后的 `With*` 调用会通过 `scope.Changed` 到达面板，重建会合并成一次投递。

**预期结果：** `SystemToolSummary` 非零（内置工具总会提供）；其余三项在对应子系统挂载前都是 `0/0`。

## 准备媒体

```csharp
using VeloxDev.AI;

var options = AgentMediaOptions.CreateVisionDefault(); // 图片上限 1280×720
var image = await AgentMedia.FromFileAsync("preview/frame.png");

Console.WriteLine($"{image.Kind} {image.MediaType} {image.Width}x{image.Height} {image.ByteCount} B");
```

`FromFileAsync` 嗅探字节而不是相信扩展名，会纠正 `image/jpg` 这类别名，并拒绝超过该类别限制的负载。包内没有编解码器、读不了的格式需要 `options.Transcoder`。

**预期结果：** 对一张符合视觉默认值的 PNG 帧，输出 `Image image/png 1280x720 <bytes> B`。
