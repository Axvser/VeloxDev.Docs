# 前置条件与安装

## 支持目标

适配器声明 `net6.0;net8.0`，并引用 `Microsoft.AspNetCore.App` 共享框架。新工程选 `net8.0`；本页跟随的 demo 在被验证时使用 `net10.0`。

- `net8.0` 需要 .NET SDK 8.0 或更高。ASP.NET Core 共享框架随 SDK 安装，不需要单独装运行时。
- 一个浏览器。即使组件在服务端运行，适配器的 JS 那一半仍在客户端跑。
- 不需要数据库、服务或 API 密钥。

## 包

| 包 | 本仓库声明的版本 | 作用 |
| --- | --- | --- |
| `VeloxDev.Razor` | 12.3.0 | 组件，以及 `wwwroot/veloxdev.workflow.js` 与 `.css` |
| `VeloxDev.Core` | 12.3.0 | 模型与画布契约，传递引入 |
| `VeloxDev.Razor.Templates` | 12.0.0 | 七个 `dotnet new` 条目模板 |

## 工程文件

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="VeloxDev.Razor" Version="12.3.0" />
  </ItemGroup>
</Project>
```

`Microsoft.NET.Sdk.Web` SDK 带来 Blazor 组件模型与静态 Web 资产。

## 注册渲染模式与资源

`Program.cs` 必须加入交互式服务端组件并映射根组件：

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// .NET 8：静态 Web 资产由 UseStaticFiles 提供。
// .NET 9+ 换成 app.MapStaticAssets()。
app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
```

`App` 是模板的 `Components/App.razor`。两个资源链接分别进入它的 `<head>` 与 `<body>`：

```html
<link rel="stylesheet" href="_content/VeloxDev.Razor/veloxdev.workflow.css" />
<!-- ... -->
<script src="_framework/blazor.web.js"></script>
```

CSS 不是可选项：表面的布局类与插槽字形尺寸都在里面。JS 模块由组件按需 import，不需要额外的 script 标签。

## 安装

```powershell
dotnet new blazor -n MyWorkflowApp
cd MyWorkflowApp
dotnet add package VeloxDev.Razor
dotnet new install VeloxDev.Razor.Templates
```

**预期结果：** 包还原成功，`Components/App.razor` 加载适配器样式表，且

```powershell
dotnet new list razor-v
```

列出 `razor-v-tree`、`razor-v-node`、`razor-v-slot`、`razor-v-link`、`razor-v-selector`、`razor-v-decorator`、`razor-v-minimap`。

## 首次构建前先生成

树组件通过 `@namespace` + `@using` 按裸类型名引用兄弟。只生成一部分无法编译。按[表面与宿主](../01_表面与宿主/index.md)一次生成全部七个；条目映射见[工作流条目模板](../../32_工作流条目模板/index.md)。

若重复注册使 `dotnet new install` 以非零码退出，先运行 `dotnet new uninstall VeloxDev.Razor.Templates`。
