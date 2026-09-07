# 弱引用类型 — 安装依赖

四个弱类型都在 `VeloxDev.Core` 包（当前版本 `8.0.0`）里的同一个命名空间 `VeloxDev.WeakTypes` 中。本特性没有单独的适配器包、没有源生成器、也不需要任何服务注册 —— 添加 Core（或项目引用它）后命名空间即可用。

## 1. 从 NuGet（消费已发布包）

```bash
dotnet add package VeloxDev.Core
```

**预期结果：** 命令以 `0` 退出，`.csproj` 中出现 `<PackageReference Include="VeloxDev.Core" Version="8.0.0" />`。因为四个类型多目标 `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`，任何能引用 `netstandard2.0` 的项目（例如 `net10.0` 控制台）都会自动获得它们。

## 2. 在本仓库中（项目引用）

要在本仓库中直接对着源码构建，给 Core 项目加一条项目引用即可。这就是最后一页快速入门控制台程序使用的确切形态（不同项目里相对路径深度不同）：

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  </ItemGroup>

</Project>
```

**预期结果：** `dotnet build` 成功；编译器从 `VeloxDev.Core` 的 `netstandard2.0` 构建产物解析这些类型 —— 那是与 `net10.0` 消费方最接近的兼容资产。

## 3. 添加 using

四个类型共享一个命名空间：

```csharp
using VeloxDev.WeakTypes;
```

**预期结果：** `WeakDelegate<>`、`WeakQueue<>`、`WeakStack<>` 与 `WeakCache<>` 都能从这个单一 `using` 解析 —— 本特性不需要其它任何命名空间。

## 运行声明

- ⚠️ NuGet 命令与 `.csproj` 形态为静态核验。第 2 节那种确切的 `<ProjectReference>` + `net10.0` 控制台形态在写本页时*确实*被编译并执行过；端到端的构建与运行记录见[验证与完整代码](../08_验证与完整代码/)页。
