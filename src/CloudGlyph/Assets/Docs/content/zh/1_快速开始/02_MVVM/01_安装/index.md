# MVVM — 安装与添加引用

运行时位于 `VeloxDev.Core` 包（命名空间 `VeloxDev.MVVM`）。生成器位于仅含分析器的包 `VeloxDev.Core.Generator`（`VeloxDev.Generators.MVVM` 与 `VeloxDev.Generators.Command`）。

## 1. 从 NuGet 安装

```bash
dotnet add package VeloxDev.Core
dotnet add package VeloxDev.Core.Generator
```

`VeloxDev.Core.csproj` 在 `Configuration != Debug` 时已经引用 `VeloxDev.Core.Generator` `10.0.0`；生成器包把 DLL 打包在 `analyzers/dotnet/cs` 下，所以普通的 `dotnet build` 就会运行它。显式添加生成器包适用于消费方配置为 `Debug`，或解决方案里另一个项目需要分析器但不需要 Core 的情况。

**预期结果：** 还原结果列出两个包；`dotnet build` 退出码为 0。

## 2. 从本仓库引用（项目引用）

项目引用**不会**传递分析器。请按 `Examples/MVVM/WPF/Demo/Demo.csproj` 的写法添加生成器项目：

```xml
<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
</ItemGroup>

<ItemGroup>
  <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                    OutputItemType="Analyzer"
                    ReferenceOutputAssembly="false"
                    Condition="'$(Configuration)' == 'Debug'" />
  <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                    Condition="'$(Configuration)' != 'Debug'" />
</ItemGroup>
```

**预期结果：** 添加一个被标注的 `partial` 类后，构建会在 `obj/<Configuration>/<TargetFramework>/generated/` 下产出 `{类名}_{命名空间}_MVVM.g.cs`（`[VeloxProperty]`）与 `{类名}_{命名空间}_Commands.g.cs`（`[VeloxCommand]`）。

## 3. 添加 using

```csharp
using VeloxDev.MVVM;
```

**预期结果：** 特性与全部运行时类型（`IVeloxCommand`、`IVeloxCommandCompletion`、`IVeloxCommandResult`、`IVeloxCommandStatus`、`IVeloxCommand<TParam, TResult>`、`VeloxCommand`、`VeloxCommandExtensions`、`CommandEventArgs`、`CommandEventType`、`CommandOutcome`、`CommandCompletion`、`ObservableCollectionTracker`）都能从这一个命名空间解析。

## 运行声明

- ⚠️ 本次文档修订未实际运行 —— 项目引用写法抄自两个 `Demo.csproj`；NuGet 路线未执行。
