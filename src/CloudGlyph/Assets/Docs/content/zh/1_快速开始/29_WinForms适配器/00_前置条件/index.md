# 前置条件与安装

## 支持目标

适配器工程声明 `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows`。新工程选 `net8.0-windows`；本页跟随的 demo 在被验证时使用 `net10.0-windows`。

- Windows。`UseWindowsForms` 与 Easel 的 GDI+ 渲染器没有其他宿主。
- `net8.0-windows` 需要 .NET SDK 8.0 或更高。若目标是 .NET Framework，需要 C# 10（`LangVersion latest`），因为生成的 ViewModel 使用了较新的 C# 语法。
- 不需要数据库、服务或 API 密钥。

## 包

| 包 | 本仓库声明的版本 | 作用 |
| --- | --- | --- |
| `VeloxDev.WinForms` | 12.3.1 | 适配器 |
| `VeloxDev.Core` | 12.3.0 | 模型与画布契约，传递引入 |
| `WinForms.Easel` | 1.1.1 | 视觉运行时，Release 下传递引入 |
| `WinForms.Easel.Generator` | 1.1.0 | 把 `.xaml` 编译成视觉控件；必须以分析器方式引用 |
| `VeloxDev.WinForms.Templates` | 12.0.0 | 七个 `dotnet new` 条目模板 |

在源码仓库内，demo 用 `Src/Adapters/VeloxDev.WinForms/VeloxDev.WinForms.csproj` 与 `Easel/Src/Generators/Easel.Generator/Easel.Generator.csproj` 两个工程引用替代这两个包。NuGet 使用者只需添加适配器包与生成器包。

## 工程文件

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <ApplicationHighDpiMode>PerMonitorV2</ApplicationHighDpiMode>
  </PropertyGroup>

  <ItemGroup>
    <!-- Easel XAML 文件的基类来自 Easel；隐式的 WinForms 命名空间会让
         Control / UserControl / Panel 在那类文件里产生歧义。 -->
    <Using Remove="System.Windows.Forms" />
    <PackageReference Include="VeloxDev.WinForms" Version="12.3.1" />
    <PackageReference Include="WinForms.Easel.Generator" Version="1.1.0"
                      OutputItemType="Analyzer" ReferenceOutputAssembly="false" />
  </ItemGroup>

  <ItemGroup>
    <AdditionalFiles Include="**/*.xaml" />
  </ItemGroup>
</Project>
```

`ApplicationHighDpiMode=PerMonitorV2` 与运行时契约一致：视觉宿主按逻辑 DIP 布局，并按 `DeviceDpi / 96` 缩放自己的 `Graphics`。

## 安装

```powershell
dotnet new winforms -n MyWorkflowApp
cd MyWorkflowApp
dotnet add package VeloxDev.WinForms
dotnet add package WinForms.Easel.Generator
dotnet new install VeloxDev.WinForms.Templates
```

**预期结果：** 包引用解析成功，且

```powershell
dotnet new list winforms-v
```

列出七个短名：`winforms-v-tree`、`winforms-v-node`、`winforms-v-slot`、`winforms-v-link`、`winforms-v-selector`、`winforms-v-decorator`、`winforms-v-minimap`。

## 首次构建前先生成

树标记按类型引用了 `GridDecorator`、`CustomTemplateSelector`、`MinimapOverlay`、`NodeView`、`SlotView` 与 `LinkView`。只生成一部分会以 `CS0246` 失败，而不是运行期报错。按[表面与宿主](../01_表面与宿主/index.md)一次生成全部七个角色；条目映射见[工作流条目模板](../../32_工作流条目模板/index.md)。

若之前留下过同短名的文件夹挂载包，`dotnet new install` 可能以非零码退出。先运行 `dotnet new uninstall VeloxDev.WinForms.Templates`，再安装 NuGet 包。
