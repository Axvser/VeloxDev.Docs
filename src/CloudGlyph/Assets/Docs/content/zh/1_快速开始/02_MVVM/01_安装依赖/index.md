# MVVM — 安装与引用

MVVM 运行时位于 `VeloxDev.Core` 包中（命名空间 `VeloxDev.MVVM`）；两个源生成器位于仅含分析器的包 `VeloxDev.Core.Generator` 中（命名空间 `VeloxDev.Generators`，类 `VeloxDev.Generators.MVVM` 与 `VeloxDev.Generators.Command`）。`VeloxDev.Core.csproj` 在除 `Debug` 之外的所有配置下把生成器声明为包依赖，所以两者一起发布时生成器会随 Core 一起被引用。

## 1. 从 NuGet 安装（使用已发布的包）

```bash
dotnet add package VeloxDev.Core
```

`Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 在 `Configuration != Debug` 时以 `PackageReference` 引用 `VeloxDev.Core.Generator` 版本 `10.0.0`。生成器包把 DLL 放在 `analyzers/dotnet/cs` 下，因此它会作为**你的项目**的分析器被还原 —— 无需手动接线。

**预期结果：** 还原输出里出现 `VeloxDev.Core.Generator`；`dotnet build` 成功，并且生成器会在你标注的类上运行。

## 2. 从本仓库引用（项目引用）

项目引用**不会**传递分析器，所以每个用到 `[VeloxProperty]` / `[VeloxCommand]` 的项目都必须自己加上生成器。演示的做法是：`Debug` 下用 analyzer 项目引用，其它配置用包引用 —— 与 `Examples/MVVM/WPF/Demo/Demo.csproj` 完全一致（不同项目的路径深度不同）：

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

  <ItemGroup>
    <ProjectReference Include="..\..\..\..\Src\Generators\VeloxDev.Core.Generator\VeloxDev.Core.Generator.csproj"
                      OutputItemType="Analyzer"
                      ReferenceOutputAssembly="false"
                      Condition="'$(Configuration)' == 'Debug'" />
    <PackageReference Include="VeloxDev.Core.Generator" Version="10.0.0"
                      Condition="'$(Configuration)' != 'Debug'" />
  </ItemGroup>

</Project>
```

**预期结果：** 只要类里有被标注的 `partial` 类，`dotnet build` 就会成功，并在 `obj/Debug/net9.0/generated/` 下产生文件（每个含 `[VeloxProperty]` 成员的类一个 `*_MVVM.g.cs`，每个含 `[VeloxCommand]` 方法的类一个 `*_Commands.g.cs`）。

## 3. 添加 using

所有 MVVM 类型都在 `VeloxDev.MVVM` 命名空间下，因此一个 `using` 就同时覆盖特性与运行时：

```csharp
using VeloxDev.MVVM;
```

**预期结果：** `VeloxPropertyAttribute`、`VeloxCommandAttribute`、`IVeloxCommand`、`IVeloxCommandCompletion`、`IVeloxCommandStatus`、`VeloxCommand`、`VeloxCommandExtensions`、`CommandEventArgs`、`CommandEventHandler`、`CommandEventType`、`CommandOutcome`、`CommandCompletion` 与 `ObservableCollectionTracker` 都能从这一个命名空间解析出来 —— 该特性不需要其它 `using`。

## 运行声明

- ✅ 2026-10-01 实际构建过（下列命令在仓库根目录执行，转录为每次构建的尾部输出）：

  ```text
  dotnet build Examples/MVVM/WPF/Demo/Demo.csproj -c Debug
  Demo -> E:\VisualStudio\Projects\VeloxDev\Examples\MVVM\WPF\Demo\bin\Debug\net9.0-windows\Demo.dll
  已成功生成。0 个警告 0 个错误

  dotnet build Examples/MVVM/Avalonia/Demo/Demo.csproj -c Debug
  Demo -> E:\VisualStudio\Projects\VeloxDev\Examples\MVVM\Avalonia\Demo\bin\Debug\net9.0\Demo.dll
  已成功生成。0 个警告 0 个错误
  ```

- 步骤 1 的 NuGet 途径**没有**执行（需要联网源）；其版本号来自 `VeloxDev.Core.csproj`。步骤 2 的项目引用写法抄自两个 `Demo.csproj`，并且**确实**被上面的构建编译过。
