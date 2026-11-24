# 生成文件

本页列出每个角色产出什么、哪些行为已经接好。生成文件是默认值，不是固定件；按你的节点类型、菜单与选择规则编辑它们。

## 文件形态

| 包 | 标记扩展名 | 成对角色 | 独立角色 | 每套文件 |
| --- | --- | --- | --- | --- |
| WPF | `.xaml` + `.xaml.cs` | tree、node、slot、link | selector、decorator、minimap | 11 |
| Avalonia | `.axaml` + `.axaml.cs` | tree、node、slot、link | selector、decorator、minimap | 11 |
| WinUI | `.xaml` + `.xaml.cs` | tree、node、slot、link | selector、decorator、minimap | 11 |
| MAUI | `.xaml` + `.xaml.cs` | tree、node、slot、link | selector、decorator、minimap | 11 |
| WinForms | `.xaml` + `.xaml.cs` | tree、node、slot、link | selector、decorator、minimap | 11 |
| Jalium | `.jalxaml` + `.jalxaml.cs` | tree、node、slot、link | selector、decorator、minimap | 11 |
| Razor | `.razor` + `.razor.cs` | tree、node、slot、link、selector、decorator、minimap | — | 14 |

内容文件替换前一律叫 `TemplateClass.*`；`-n` 同时改文件名与类名。

## 每个角色接了什么

| 角色 | 生成内容 |
| --- | --- |
| tree | 表面部件（`PART_Canvas`、`PART_ScrollViewer`、`PART_GridDecorator`、`PART_SurfaceBorder`、`PART_MinimapOverlay`）、节点/连线模板、选择器资源、空的连线菜单，以及表面的附着属性或组件参数。 |
| node | 设计尺寸卡片、带节点拖动的标题条、带槽布局的命名槽部件与端口包装。 |
| slot | 带插槽连线行为的槽字形；Razor 上还会打开槽布局与连线组件。 |
| link | 一条连线一个视图。XAML 包发布曲线供命中测试；Jalium 另外在绘制前调用 `WorkflowLinkBounds.Apply`。 |
| selector | `ViewPool.TemplateSelector` / `ViewSourcePipeline` 分发。WinForms 派生 `Easel.Visuals.VisualTemplateSelector`；Jalium 派生 `DataTemplateSelector`；Razor 的选择器是包着 `ViewPool` 的组件。 |
| decorator | 实现 `IWorkflowGridDecorator` 的网格与标尺绘制；默认标尺厚度 28，Jalium 为 36。 |
| minimap | 实现 `IWorkflowMinimapOverlay` 的缩略图与视口块；平台支持时带拖拽平移。 |

## 连线菜单默认是空的

树声明并接好菜单与右键，但不加条目。

| GUI | 条目放在哪 |
| --- | --- |
| WPF / Avalonia / WinUI / MAUI / Jalium | 由 `WorkflowSurfaceBehavior.LinkMenuKey` 命名的资源（`ContextMenu` / `MenuFlyout`）；`Command="{Binding DeleteCommand}"` |
| WinForms | 树的 `VisualContextMenu x:Key="LinkContextMenu"`，或宿主的 `SetLinkMenuBuilder(this, …)` |
| Razor | 树里的 `<LinkMenu Context="link">` 片段；每个条目是内联 `@onclick` |

每个条目都接收被右击的连线，所以一行就是完整动作。

## 跨平台复制会坏的差异

- **连线策略。** MAUI 把所有连线画在一个视口级覆盖层；WinForms 与 XAML 包为每条连线实例化一个视图。跨这条边界复制连线视图会得到一个能编译、却没有连线的画布。
- **标尺厚度。** 包默认 28，Jalium 为 36。从装饰器读 `RulerBand`，并把它用于画布平移、网格数学与虚拟化内缩。
- **Avalonia 的占位类型。** `vm:TreeViewModel` 是你的类型，不是生成的。未改指向前构建失败是刻意的。
- **Jalium 的变换镜像。** 树类必须重新暴露 `CanvasTransform`；没有它，平移后所有卡片都停在世界原点。
- **调试 HUD 不在任何包里。** demo 带 `InfoOverlay`；需要就自己加。

## 构建才是检查

`dotnet new` 只做字符串替换，不理解内容；生成成功什么也证明不了。

```powershell
dotnet new winforms-v-tree -n TreeView -ns MyWorkflowApp.Views -o Views
# … 其余六个角色，同一个 -ns …
dotnet build
```

**预期结果：** `dotnet build` 以 `0` 退出，应用显示表面。生成的套件只有在对适配器编译并运行正确时才算正确。

### 备注

- 仓库的 `* Trimmed` demo 是这些角色的最小调用序列镜像，不是 publish-trim 或 AOT 验证。
- 部分套件会以 `CS0246` 失败，因为树类型引用了它的兄弟。
- 颜色选项没效果时改生成文件；见[生成选项](../02_生成选项/index.md)的惰性符号表。
