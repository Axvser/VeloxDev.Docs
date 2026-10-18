# 安装

## 从 NuGet 安装

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="VeloxDev.Core" Version="10.0.0" />
  </ItemGroup>
</Project>
```

发布包把 `VeloxDev.Core.Generator` 声明为包依赖；该包把 DLL 放在 `analyzers/dotnet/cs` 下，因此两个生成器（`VeloxDev.Generators.AopSurface`、`VeloxDev.Generators.AopProxy`）会自动参与消费方的编译。

或者：

```bash
dotnet add package VeloxDev.Core --version 10.0.0
```

**预期结果：** 命令以 `0` 退出，`PackageReference` 出现在 `.csproj` 中，还原完成。

## 在仓库内部引用

`ProjectReference` **不会**传递分析器。随仓库的 Demo 因此单独把生成器作为分析器引入 —— 即 `Examples/AOP/WPF/Demo/Demo.csproj` 的写法：

```xml
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

缺少分析器引用时，`[AspectOriented]` 本身仍能编译，但不会生成 `Aop()` 扩展与代理类 —— 失败表现为调用处的“成员不存在”编译错误，而不是警告。

**预期结果：** `dotnet build` 成功；设置 `EmitCompilerGeneratedFiles=true` 后，分析器输出目录中每个目标类有三个文件：`<Interface>.g.cs`、`<Interface>Proxy.g.cs`、`<Class>_<Ns>_AopExt.g.cs`。
