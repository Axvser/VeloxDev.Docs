# 工作流系统 — 安装 / 添加依赖

#### 1. 新建控制台项目

```bash
dotnet new console -n WorkflowCalc -f net9.0
cd WorkflowCalc
```

**预期结果：** 目录出现 `WorkflowCalc.csproj`，`dotnet build` 退出码 0。

#### 2. 添加核心包

核心引擎（编译、运行时、`[WorkflowBuilder.*]`）全部在 `VeloxDev.Core` 里：

```bash
dotnet add package VeloxDev.Core
```

该包会传递 `VeloxDev.Core.Generator`（Roslyn 源码生成器，Analyzer）与 `Microsoft.Bcl.HashCode`。需要整树 JSON 序列化时再添加扩展包：

```bash
dotnet add package VeloxDev.Core.Extension
```

`VeloxDev.Core.Extension` 提供 `VeloxDev.MVVM.Serialization.ComponentModelEx`（`Serialize` / `Deserialize`），本指南在 [06 序列化](../06_序列化/index.md) 用到。

**预期结果：** `.csproj` 的 `<ItemGroup>` 中出现对应 `PackageReference`；`dotnet restore` 成功。

#### 3. 在本仓库内联调（可选、本次实测的路径）

若直接基于本仓库源码验证（本次实测所用），用 `ProjectReference` 指向本地工程，效果等价：

```xml
<ItemGroup>
    <ProjectReference Include="Src\Core\VeloxDev.Core\VeloxDev.Core.csproj" />
    <ProjectReference Include="Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj" />
</ItemGroup>
```

源码生成器会经 `VeloxDev.Core` 的传递引用自动应用到本项目 —— 无需手动引用生成器。

**预期结果：** 还原无错误；`using VeloxDev.WorkflowSystem;`、`using VeloxDev.Core.WorkflowSystem.CompilerEx;`、`using VeloxDev.MVVM;`、`using VeloxDev.MVVM.Serialization;` 均可解析。

## 下一步

依赖就绪后，在 [02 定义组件](../02_定义组件/index.md) 声明 Tree / Slot / Node 与节点 Helper。
