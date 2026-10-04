# 平台适配器 — 完整代码

下面的七个子页面**逐字重现**「配置」页 `dotnet new wpf-v-*` 命令所生成的文件（`-n` 名称与 `Demo.Views.Workflow` 命名空间已代入，模板默认颜色已填好）。合起来就是 WPF 工程的工作流**视图层**。

## 工程文件

该套件位于启用 `UseWPF` 并包引用适配器的 WPF 工程里：

```xml
<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <OutputType>WinExe</OutputType>
        <TargetFramework>net9.0-windows</TargetFramework>
        <Nullable>enable</Nullable>
        <ImplicitUsings>enable</ImplicitUsings>
        <UseWPF>true</UseWPF>
    </PropertyGroup>
    <ItemGroup>
        <PackageReference Include="VeloxDev.WPF" Version="10.0.0" />
    </ItemGroup>
</Project>
```

要*看到*工作流，还需要一个应用外壳（`App` + `MainWindow`）来承载 `WorkflowView`，并把它的 `DataContext` 绑定到用 `[WorkflowBuilder.Tree]` 构建的 `IWorkflowTreeViewModel`——构树属于「工作流系统」特性，不属于本页。下面的视图文件本身是框架完整的，只差这个数据上下文。

子页面（每个源文件一页）：

- [00 WorkflowView — 表面宿主](00_工作流视图/index.md)
- [01 NodeView — 节点卡片](01_节点视图/index.md)
- [02 SlotView — 连接器](02_插槽视图/index.md)
- [03 LinkView — 曲线连线](03_连线视图/index.md)
- [04 GridDecorator — 网格与标尺](04_网格装饰器/index.md)
- [05 MinimapOverlay — 小地图](05_小地图浮层/index.md)
- [06 TemplateSelector — DataTemplate 选择器](06_模板选择器/index.md)

## 运行声明

- ✅ 已于 2026-10-01 生成并比对。[配置](../02_环境配置/index.md)页的七条 `dotnet new wpf-v-*` 命令已针对已安装的 `VeloxDev.WPF.Templates` 包实际运行，在 `Views/` 下恰好生成 **11 个文件**：

```text
已成功创建模板“VeloxDev WPF Workflow Tree View”。
已成功创建模板“VeloxDev WPF Workflow Node View”。
已成功创建模板“VeloxDev WPF Workflow Slot View”。
已成功创建模板“VeloxDev WPF Workflow Link View”。
已成功创建模板“VeloxDev WPF Workflow Template Selector”。
已成功创建模板“VeloxDev WPF Workflow Grid Decorator”。
已成功创建模板“VeloxDev WPF Workflow Minimap Overlay”。
```

  随后把七个子页面上的代码块与生成文件逐字节比对：**11 个中有 9 个逐字一致**；不一致的两个（`WorkflowView.xaml` 漏了 `CornerRadius="3"`，`NodeView.xaml` 一处注释被写坏）已修正为与生成结果一致。
- ✅ 承载该视图层的演示也在同日构建通过：`dotnet build Examples/Workflow/WPF/Demo/Demo.csproj` 成功，0 警告 / 0 错误（见[验证](../04_验证/index.md)页运行声明）。
- ⚠️ 该脚手架未*单独*编译（它被生成到临时目录而非 WPF 工程里），组装后的应用也未启动——因此应视为「经生成 + 经等价仓库内演示构建」的验证，而非这套确切脚手架的端到端实跑。
