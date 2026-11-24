# 验证与完整脚本

## 构建即检查

生成成功什么也证明不了：`dotnet new` 只做文本替换，不理解内容。门槛是：

```powershell
dotnet build
```

一套生成物正确，指的是它能对着适配器编译，并且应用能显示表面。本仓库的校验脚本机械地做同一件事：打包、安装、生成全部七个、一起编译，并对仍残留 `replaces` 占位符的文件报错。

## 真会撞上的失败

| 症状 | 原因 | 修法 |
| --- | --- | --- |
| 树找不到节点视图，或兄弟类型报 `CS0246` | 七个条目进了不同命名空间；兄弟被改名；少生成了一个兄弟 | 一个命名空间、默认名、七个条目齐全 |
| Avalonia：在 `x:DataType="vm:TreeViewModel"` 处构建失败 | 包故意放了一个指向你 ViewModel 命名空间的占位类型 | 把 `xmlns:vm` 指向你的命名空间并改类型名；这个失败是刻意的 |
| 某个颜色选项毫无效果 | 该 GUI 没有这个值的消费者 | 直接改生成文件；对照[定制](../02_定制/index.md)里的惰性符号表 |
| 连线菜单打开后没有 Delete 条目 | 包声明并接好了菜单，但不加条目 | 往资源、片段或 `SetLinkMenuBuilder` 调用里加条目 |
| 节点文字被挤压，缩小时裁切 | 内层设计网格绑到了塌缩后的 `Size`，而外层容器已经缩放 | 把内层网格钉在 `260 × 180`，让容器缩放 |
| 端口的半边藏进卡片下面 | 端口位于裁剪容器里，或被卡面盖住 | 给端口 `ZIndex="6"`，并让卡片及其祖先不裁剪 |
| 槽的视觉状态永远不变 | 视图绑了 `Slot.State` 而不是槽自己的 `State` | 把槽控件的 `DataContext` 设为槽，并从它读 `State` |
| 改过视图后连线或悬停失灵 | `SlotView` 被换成普通图形，手势与测量一起没了 | 保留 `SlotView`，或恰好在外面包一次 `WorkflowSlotConnectionBehavior` |
| 刻度与节点逐渐错位 | 画布平移用的标尺值和 `RulerBand` 不一致 | 读 `RulerBand`，并用它做平移、网格数学与虚拟化 inset |
| `dotnet new` 解析到旧包，或安装以非零码退出 | 重复注册，或同短名的文件夹挂载包 | `dotnet new uninstall VeloxDev.<GUI>.Templates`，再装 NuGet 包 |

## 完整脚本

在工程目录运行。它安装模板包与适配器，用默认名生成整套视图，然后构建。

```powershell
dotnet new install VeloxDev.WinForms.Templates
dotnet add package VeloxDev.WinForms

dotnet new winforms-v-tree      -n TreeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-node      -n NodeView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-slot      -n SlotView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-link      -n LinkView              -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-selector  -n CustomTemplateSelector -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-decorator -n GridDecorator         -ns MyWorkflowApp.Views -o Views
dotnet new winforms-v-minimap   -n MinimapOverlay        -ns MyWorkflowApp.Views -o Views

dotnet build
```

换另一个 GUI 时，把 `VeloxDev.WinForms.Templates` 与 `VeloxDev.WinForms` 换成目标包与适配器，并换掉 `winforms-v-` 前缀。七条 `-ns` 保持一致。Razor 每个条目产出 `.razor` + `.razor.cs` 一对，所以整套是十四个文件。

符号来源：

- 全部 49 个短名与七个条目 identity —— `Src/Templates/VeloxDev.<Platform>.Templates/working/content/workflow-<role>/.template.config/template.json`。
- 生成物的形状 —— `Src/Templates/.../TemplateClass.*`，镜像在 `Examples/Workflow/<GUI> Trimmed/Demo/`（Razor 为 `Blazor Trimmed`）。
- 包元数据（`PackageType=Template`、`netstandard2.0`、版本 12.0.0）—— `Src/Templates/VeloxDev.<Platform>.Templates/working/VeloxDev.<Platform>.Templates.csproj`。

## 运行声明

⚠️ 未实际运行 —— 2026-11-25 仅对照 `Src/Templates/` 静态核验。49 个短名与 identity 读自每个 `template.json`；脚本本身没有在这里执行，因此没有记录构建输出。
