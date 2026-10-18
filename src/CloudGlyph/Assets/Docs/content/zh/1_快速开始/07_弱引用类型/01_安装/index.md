# 弱引用类型 — 安装

四个弱引用类型都在 `VeloxDev.Core` 包中（当前版本 `10.0.0`），命名空间统一为 `VeloxDev.WeakTypes`。本功能没有独立的适配器包、没有源生成器、也没有服务注册——添加 Core（或引用它）之后该命名空间即可用。

## 1. 从 NuGet 安装（使用已发布包）

```bash
dotnet add package VeloxDev.Core
```

**预期结果：** 命令以 `0` 退出，`.csproj` 中出现 `<PackageReference Include="VeloxDev.Core" Version="10.0.0" />`。由于四个类型多目标为 `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` / `net8.0`，任何能引用其中之一的项目都会自动获得它们。

## 2. 从本仓库引用（项目引用）

若要针对本仓库源码构建，给 Core 项目添加项目引用。最后一页的控制台程序正是这种形状（相对路径深度随项目位置而变）：

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

**预期结果：** `dotnet build` 成功；`net10.0` 消费者会选用 `VeloxDev.Core` 的 `net8.0` 构建（最近的兼容资产），而不是 `netstandard2.0` 构建。

## 3. 添加 using

四个类型共用一个命名空间：

```csharp
using VeloxDev.WeakTypes;
```

**预期结果：** `WeakDelegate<>`、`WeakQueue<>`、`WeakStack<>` 与 `WeakCache<>` 都由这一条 `using` 解析出来——本功能不需要其它命名空间。
