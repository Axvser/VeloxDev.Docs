# 安装准备

## 前置条件

- **支持的目标框架：** `netstandard2.0` 与 `net8.0`，见 `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`。
- **SDK：** .NET SDK 8.0 或更新；测试运行在 .NET 10。
- **包：** `VeloxDev.Core.Extension` 12.3.0，引用 `ModelContextProtocol` 2.2.0。
- **本地服务器：** 对应模式需要的运行环境在 `PATH` 上——Node 的 `node`/`npm`/`npx`、`uvx` 的 `uv`、`Pip` 的 Python 与 `pip`、`Dotnet` 的 .NET 运行时，或 `Exe` 的可执行文件。
- **HTTP 服务器：** 能访问该端点。
- **解析配置或查看已注册服务器不需要模型。**

## 安装

```powershell
dotnet new console -n McpQuickStart
cd McpQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**预期结果：** `dotnet list package` 中能看到 `VeloxDev.Core.Extension` 与 `ModelContextProtocol`。

## 创建 scope

```csharp
using VeloxDev.AI.MCP;

var mcp = new McpScope()
    .WithSynchronizationContext(SynchronizationContext.Current ?? new SynchronizationContext());
```

`WithSynchronizationContext` 让状态视图模型在宿主线程更新。无界面宿主可以省略；绑定 UI 时必须设置。

**预期结果：** `mcp.Status.Servers` 是空集合，`mcp.RegisteredServers` 也是空。

## 配置一个远程服务器

```csharp
var learn = new McpServerConfiguration
{
    Name = "Microsoft Learn",
    Description = "通过 Streamable HTTP 检索 Microsoft 文档。",
    RunMode = McpServerRunMode.Http,
    Endpoint = "https://learn.microsoft.com/api/mcp",
    Options = new Dictionary<string, object?>
    {
        ["connectionTimeout"] = 30,
    },
};

mcp.WithServers(learn);
Console.WriteLine(mcp.RegisteredServers.Count); // 1
```

`WithServers` 只**预注册**智能体之后可以按名装载的配置，不连接任何东西。

**预期结果：** 输出 `1`。因为什么都没装载，`mcp.Status.Servers` 仍为空。

## 配置一个本地服务器

```csharp
var files = new McpServerConfiguration
{
    Name = "Filesystem (npx)",
    RunMode = McpServerRunMode.Npx,
    Package = "@modelcontextprotocol/server-filesystem",
    Arguments = ["C:/data"],
    Options = new Dictionary<string, object?>
    {
        ["env"] = new Dictionary<string, object?> { ["FILESYSTEM_ROOT"] = "C:/data" },
    },
};

mcp.WithServers(files);
```

`Npx` 模式下 `Package` 是 npm 包名，`Arguments` 跟在它后面传入。`Normal` 模式下 `Package` 就是原样执行的命令，没有安装步骤。

**预期结果：** `mcp.RegisteredServers.Count` 为 `2`。

## 什么会被拒绝

`Options` 只接受已知键：`headers`、`oauth`、`connectionTimeout`、`transportMode`、`ownsSession`、`env`、`workingDirectory`。未知键会在装载服务器时抛错，而不是被静默忽略。

**预期结果：** 加入 `["timout"] = 5` 再调用 `LoadAsync`，异常里会点名该键。
