# 01 · 安装依赖与添加分析器

本特性需要两个包：运行期库与源生成器。生成器是**分析器**，因此不得在运行期被引用 —— 项目引用要写 `ReferenceOutputAssembly="false"`，包引用要按分析器包含。

## 1. 创建工程

```text
dotnet new console -n TickDemo
cd TickDemo
```

**预期结果：** 生成 `TickDemo` 目录，其中有 `TickDemo.csproj` 与 `Program.cs`；`dotnet run` 输出 `Hello, World!`。

## 2. 添加运行期库

```text
dotnet add package VeloxDev.Core --version 10.0.0
```

**预期结果：** `VeloxDev.Core` 出现在 `TickDemo.csproj` 的 `<PackageReference>` 列表中，`dotnet build` 能无错还原。

## 3. 添加生成器

从 NuGet 安装：

```text
dotnet add package VeloxDev.Core.Generator --version 10.0.0
```

然后确保该包被当作分析器而不是普通库。在 `TickDemo.csproj` 中：

```xml
<ItemGroup>
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
  </PackageReference>
</ItemGroup>
```

或者，在本仓库内工作时，像演示那样直接引用生成器工程 —— `Examples/Tickable/WPF/Demo/Demo.csproj` 第 15-23 行：

```xml
<!-- 本项目用 [Tickable]，analyzer 不随 ProjectReference 传递。 -->
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

**预期结果：** `dotnet build` 成功。若分析器缺失，构建期**不会**报错；你会在使用那些生成成员的那一刻拿到 `CS0103` / `CS0535`。这个失败模式值得记住：一个声明了 `partial` 却没有变成 `ITickable` 的类，几乎总是意味着生成器没有挂上。

## 4. 确认生成器已挂上

在 `Program.cs` 里加一个一次性类并构建：

```csharp
using VeloxDev.TimeLine;

[Tickable]
public partial class Probe
{
}

// Program.cs
Console.WriteLine(typeof(Probe).GetInterfaces().Length);
```

**预期结果：** 工程构建成功。想看到生成文件，请加 `-p:EmitCompilerGeneratedFiles=true` 构建；文件会落在

```text
obj/Debug/<tfm>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.Tickable/<类名>_<命名空间片段>_Tick.g.cs
```

命名空间 `TickVerify` 下的 `BouncingBall` 对应 `BouncingBall_TickVerify_Tick.g.cs`；位于全局命名空间的类，片段为 `Global`。不加 `EmitCompilerGeneratedFiles` 时该文件根本不会落盘 —— 它不在那儿，并不能证明生成器没运行。如果生成的成员在编译中不存在，就是分析器没挂上，回到第 3 步检查。
