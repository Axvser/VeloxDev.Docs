# 生成一套视图

一套视图是一个宿主加六个部件。七个都要生成：装饰器画浮动标尺带，小地图提供缩略图，树按类型引用其余角色。

## 49 个短名

每个短名都是 `{前缀}-v-{后缀}`。七个包与七个角色给出这张矩阵。

| 角色 | WPF | Avalonia | WinUI | MAUI | WinForms | Razor | Jalium |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tree | `wpf-v-tree` | `ava-v-tree` | `winui-v-tree` | `maui-v-tree` | `winforms-v-tree` | `razor-v-tree` | `jalium-v-tree` |
| node | `wpf-v-node` | `ava-v-node` | `winui-v-node` | `maui-v-node` | `winforms-v-node` | `razor-v-node` | `jalium-v-node` |
| slot | `wpf-v-slot` | `ava-v-slot` | `winui-v-slot` | `maui-v-slot` | `winforms-v-slot` | `razor-v-slot` | `jalium-v-slot` |
| link | `wpf-v-link` | `ava-v-link` | `winui-v-link` | `maui-v-link` | `winforms-v-link` | `razor-v-link` | `jalium-v-link` |
| selector | `wpf-v-selector` | `ava-v-selector` | `winui-v-selector` | `maui-v-selector` | `winforms-v-selector` | `razor-v-selector` | `jalium-v-selector` |
| decorator | `wpf-v-decorator` | `ava-v-decorator` | `winui-v-decorator` | `maui-v-decorator` | `winforms-v-decorator` | `razor-v-decorator` | `jalium-v-decorator` |
| minimap | `wpf-v-minimap` | `ava-v-minimap` | `winui-v-minimap` | `maui-v-minimap` | `winforms-v-minimap` | `razor-v-minimap` | `jalium-v-minimap` |

后缀是 `-decorator`，不是 `-grid`。每个条目背后的 identity 是 `VeloxDev.<Platform>.Workflow<Role>`，例如 `VeloxDev.WinForms.WorkflowTreeView`。

## 七条命令

一个包、七个角色、一个命名空间：

```powershell
dotnet new winforms-v-tree      -n TreeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-node      -n NodeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-slot      -n SlotView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-link      -n LinkView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-selector  -n CustomTemplateSelector -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views -o Views
dotnet build
```

把前缀换成另一个 GUI（`wpf`、`ava`、`winui`、`maui`、`razor`、`jalium`）。七条命令的 `-ns` 必须保持一致。

| GUI | 选择器默认名 | 每套文件数 |
| --- | --- | --- |
| WPF、Avalonia、WinUI、MAUI、WinForms、Jalium | `TemplateSelector`（WinForms 为 `CustomTemplateSelector`） | 11：四对标记 + 三个 `.cs` |
| Razor | `TemplateSelector` | 14：七对 `.razor` + `.razor.cs` |

WinForms、Razor 与 Jalium 的逐家命令块在各自的适配器快速开始里：[WinForms](../../29_WinForms适配器/01_表面与宿主/index.md)、[Razor](../../30_Razor适配器/01_表面与宿主/index.md)、[Jalium](../../31_Jalium适配器/01_表面与宿主/index.md)。

## `-n`、`-ns` 与 `-o` 各做什么

- `-n` 设置类名与文件名。`sourceName: "TemplateClass"` 是替换锚，因此它也会改写 `x:Class` 与所有对该类的引用。
- `-ns` 在每个生成文件里替换 `TemplateNamespace`。七个必须一致。
- `-o` 是输出目录。每个条目的 `preferNameDirectory` 都是 `false`，所以 `-o Views` 直接写进 `Views/`，不会按名字再建子目录。

**默认名是承重的。** 树把 `NodeView`、`SlotView`、`LinkView`、`TemplateSelector`（或 `CustomTemplateSelector`）、`GridDecorator` 与 `MinimapOverlay` 写进标记或组件树。若给某个条目传了非默认 `-n`，必须在同一次改动里改树的引用；没有别的地方会报告这处错配。

## 预期结果

- 七条 `dotnet new` 都以 0 退出。
- `Views/` 含整套视图：标记类包 11 个文件，Razor 14 个。
- `dotnet build` 以 0 退出。生成成功本身什么也证明不了：`dotnet new` 只做文本替换，不理解内容。

若构建失败，先读[验证与完整脚本](../03_验证/index.md)，再动生成文件。
