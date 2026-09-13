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
        <PackageReference Include="VeloxDev.WPF" Version="9.0.0" />
    </ItemGroup>
</Project>
```

要*看到*工作流，还需要一个应用外壳（`App` + `MainWindow`）来承载 `WorkflowView`，并把它的 `DataContext` 绑定到用 `[WorkflowBuilder.Tree]` 构建的 `IWorkflowTreeViewModel`——构树属于「工作流系统」特性，不属于本页。下面的视图文件本身是框架完整的，只差这个数据上下文。

子页面（每个源文件一页）：

- [00 WorkflowView — 表面宿主](00_工作流视图/index.md)
- [01 NodeView — 节点卡片](01_节点视图/index.md)
- [02 SlotView — 连接器](02_插槽视图/index.md)
- [03 LinkView — 折线连线](03_连线视图/index.md)
- [04 GridDecorator — 网格与标尺](04_网格装饰器/index.md)
- [05 MinimapOverlay — 小地图](05_小地图浮层/index.md)
- [06 TemplateSelector — DataTemplate 选择器](06_模板选择器/index.md)

## 运行声明

- ⚠️ 未实际运行 — 仅静态核验。每段代码都取自 `Src/Templates/VeloxDev.WPF.Templates/working/content` 下的真实模板源码（符号已替换为默认值），并与 `Src/Adapters/VeloxDev.WPF` 的适配器 API 面交叉核对；文件针对该 API 面可编译，但本环境未真正编译或执行，因此这套脚手架应视为「经检查而非经运行」的验证。
