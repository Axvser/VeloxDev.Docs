# MVVM — 安装与引用

MVVM 运行时与两个源生成器住在同两个包里：`VeloxDev.Core`（命名空间 `VeloxDev.MVVM` 下的运行时类型）以及它的分析器包 `VeloxDev.Core.Generator`（生成器类 `VeloxDev.Generators.MVVM` / `VeloxDev.Generators.Command`）。`VeloxDev.Core.csproj` 以同版本引用生成器，因此添加 Core 即可把生成器一起带进来。

## 1. 从 NuGet（消费已发布的包）

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core`（当前为 `9.0.0`）把 `VeloxDev.Core.Generator` `9.0.0` 声明为包依赖（`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`），于是生成器程序集作为*你项目*的分析器被还原 —— 无需手动接线分析器。

**预期结果：** 还原输出列出 `VeloxDev.Core.Generator`；`dotnet build` 成功。

## 2. 从本仓库（项目引用）

所有仓库内的演示都走这条路 —— 直接项目引用 Core 源工程：

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  </ItemGroup>

</Project>
```

这正是 `Examples/MVVM/WPF/Demo/Demo.csproj` 与 `Examples/MVVM/Avalonia/Demo/Demo.csproj` 里的引用形态（不同工程的相对路径深度不同）。从源码构建 Core 会把生成器编入构建并喂给引用它的工程，因此当你标注成员后会出现生成的 `.g.cs` 文件。

**预期结果：** 添加引用后 `dotnet build` 成功；在下一页第 1 步标注的 partial 类会生成到 `obj/<配置>/<目标框架>/generated/` 下（例如 `CounterViewModel_QuickStart_Mvvm_MVVM.g.cs` 与 `CounterViewModel_QuickStart_Mvvm_Commands.g.cs`）。

## 3. 添加 using

每个 MVVM 类型都在命名空间 `VeloxDev.MVVM` 里。承载特性的文件需要它：

```csharp
using VeloxDev.MVVM;
```

**预期结果：** `VeloxPropertyAttribute`、`VeloxCommandAttribute`、`IVeloxCommand`、`VeloxCommand`、`CommandEventArgs`、`CommandEventHandler`、`CommandEventType`、`ObservableCollectionTracker` 都能从这个单一命名空间解析 —— 该特性不需要其它 `using`。

## 运行声明

- ⚠️ 仅静态核验 —— 编写本页时未编译或运行任何内容。版本号与生成器依赖来自 `VeloxDev.Core.csproj`；引用形态来自 MVVM 演示的 `Demo.csproj`。
