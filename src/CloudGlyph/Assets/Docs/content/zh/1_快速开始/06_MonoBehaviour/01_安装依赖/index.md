# MonoBehaviour — 安装依赖

运行时类型与源生成器住在两个包里。`VeloxDev.Core`（当前为 `8.0.0`）在 `VeloxDev.TimeLine` 与 `VeloxDev.MonoBehaviour` 命名空间中声明运行时；它的 `VeloxDev.Core.csproj` 以同版本引用分析器包 `VeloxDev.Core.Generator`，所以添加 Core 即可把 `[MonoBehaviour]` 生成器带进来。除此之外无需任何配置 —— 循环不需要 UI 适配器，也不需要注册服务。

## 1. 从 NuGet（消费已发布的包）

```bash
dotnet add package VeloxDev.Core
```

因为 `VeloxDev.Core`（当前版本 `8.0.0`）把 `VeloxDev.Core.Generator` `8.0.0` 声明为包依赖，生成器程序集会作为*你项目*的分析器自动还原。仓库内 WPF 演示只项目引用了 `VeloxDev.Core`，其 `[MonoBehaviour]` 类仍能编译 —— 这说明无需单独引用分析器，也无需手动接线。

**预期结果：** 还原输出列出 `VeloxDev.Core.Generator`；`dotnet build` 成功，且（[定义行为](../02_定义行为/)页中的）`[MonoBehaviour]` 类被编译成 `IMonoBehaviour` 实现。

## 2. 从本仓库（项目引用）

仓库内的演示走项目引用，直接引用 Core 源工程。下面是 `Examples/MonoBehaviour/WPF/Demo/Demo.csproj` 的引用形态（不同工程的相对路径深度不同）：

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net10.0-windows</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <UseWPF>true</UseWPF>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  </ItemGroup>

</Project>
```

从源码构建 Core 会把生成器编入构建并喂给引用它的工程，因此你一旦标注某个类就会出现 `.g.cs` partial。

**预期结果：** 添加引用后 `dotnet build` 成功；下一步中标注的类会让编译器生成名为 `{ClassName}_{NamespaceWithDotsAsUnderscores}_Mono.g.cs` 的 partial（例如 `FrameCounter_MonoQuickStart_Mono.g.cs`）。

## 3. 添加 using

特性与管理器都在 `VeloxDev.TimeLine`。你自己的文件只需要这一个命名空间即可解析特性、管理器与 `FrameEventArgs` 参数类型。生成的代码自己引用接口命名空间 `VeloxDev.MonoBehaviour`，你无需输入它：

```csharp
using VeloxDev.TimeLine;
```

**预期结果：** `MonoBehaviourAttribute`、`MonoBehaviourManager`、`FrameEventArgs` 与通道事件参数都能从这个单一命名空间解析 —— 该特性不需要其它 `using`。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未执行包命令与 `.csproj` 形态。版本号来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`；引用形态来自 `Examples/MonoBehaviour/WPF/Demo/Demo.csproj`。端到端的构建与运行记录在[验证与完整代码](../06_验证与完整代码/)页。
