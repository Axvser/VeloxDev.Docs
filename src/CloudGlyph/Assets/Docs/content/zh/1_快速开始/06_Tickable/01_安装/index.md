# 安装并接入分析器

本特性需要两个包：运行库与源生成器。生成器是**分析器**，不能在运行时被引用。

## 1. 创建项目

```text
dotnet new console -n TickDemo
cd TickDemo
```

**预期结果：** 生成 `TickDemo` 目录，其中包含 `TickDemo.csproj` 与 `Program.cs`；`dotnet run` 输出 `Hello, World!`。

## 2. 添加运行库

```text
dotnet add package VeloxDev.Core --version 10.0.0
```

**预期结果：** `TickDemo.csproj` 的 `<PackageReference>` 中出现 `VeloxDev.Core`，且 `dotnet build` 能无错还原。

## 3. 添加生成器

```text
dotnet add package VeloxDev.Core.Generator --version 10.0.0
```

包会把生成器放在 `analyzers/dotnet/cs` 下，所以 `dotnet add package` 就够了 —— 包引用的分析器不需要 `OutputItemType`。为了不把分析器带进你自己的包依赖，把它标记为私有：

```xml
<ItemGroup>
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

在本仓库内工作时，按示例的方式引用生成器工程（`Examples/Tickable/WPF/Demo/Demo.csproj` 第 15-23 行）—— `ProjectReference` **不会**把分析器传递给引用方：

```xml
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

**预期结果：** `dotnet build` 成功。若分析器缺失，构建仍然成功 —— 失败要到你使用生成的表面时才出现：`CS0103`（「当前上下文中不存在名称 'InitializeTickable'」）或入口方法上的 `CS1061`。一个标了 `partial` 却始终没有变成 `ITickable` 的类，几乎总是意味着生成器没接上。

## 4. 确认生成器已接入

添加一个探针类并构建：

```csharp
using VeloxDev.TimeLine;

[Tickable]
public partial class Probe
{
}

public static class Program
{
    public static void Main()
        => Console.WriteLine(typeof(Probe).GetInterfaces().Length);
}
```

**预期结果：** 程序输出 `1` —— `Probe` 实现了 `VeloxDev.TimeLine.ITickable`。要查看生成的文件，用 `-p:EmitCompilerGeneratedFiles=true` 构建，它会落在

```text
obj/Debug/<tfm>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Tickable/<ClassName>_<NamespaceSegment>_Tick.g.cs
```

命名空间 `TickVerify` 中的 `BouncingBall` 会生成 `BouncingBall_TickVerify_Tick.g.cs`；全局命名空间中的类得到段名 `Global`。不加 `EmitCompilerGeneratedFiles` 时该文件根本不会写到磁盘 —— 它不在那里并不能证明生成器没运行。
