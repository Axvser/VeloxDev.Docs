# 短名称

每个短名都是 `{prefix}-v-{suffix}`。七个前缀与七个角色后缀给出完整的 49 名矩阵。

## 49 个短名

| 角色 | WPF | Avalonia | WinUI | MAUI | WinForms | Razor | Jalium |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tree | `wpf-v-tree` | `ava-v-tree` | `winui-v-tree` | `maui-v-tree` | `winforms-v-tree` | `razor-v-tree` | `jalium-v-tree` |
| node | `wpf-v-node` | `ava-v-node` | `winui-v-node` | `maui-v-node` | `winforms-v-node` | `razor-v-node` | `jalium-v-node` |
| slot | `wpf-v-slot` | `ava-v-slot` | `winui-v-slot` | `maui-v-slot` | `winforms-v-slot` | `razor-v-slot` | `jalium-v-slot` |
| link | `wpf-v-link` | `ava-v-link` | `winui-v-link` | `maui-v-link` | `winforms-v-link` | `razor-v-link` | `jalium-v-link` |
| selector | `wpf-v-selector` | `ava-v-selector` | `winui-v-selector` | `maui-v-selector` | `winforms-v-selector` | `razor-v-selector` | `jalium-v-selector` |
| decorator | `wpf-v-decorator` | `ava-v-decorator` | `winui-v-decorator` | `maui-v-decorator` | `winforms-v-decorator` | `razor-v-decorator` | `jalium-v-decorator` |
| minimap | `wpf-v-minimap` | `ava-v-minimap` | `winui-v-minimap` | `maui-v-minimap` | `winforms-v-minimap` | `razor-v-minimap` | `jalium-v-minimap` |

后缀是 `-decorator`，不是 `-grid`。

## 每个平台的标识

| 前缀 | 包 | 标识段 | 示例标识 |
| --- | --- | --- | --- |
| `wpf` | `VeloxDev.WPF.Templates` | `VeloxDev.WPF` | `VeloxDev.WPF.WorkflowNodeView` |
| `ava` | `VeloxDev.Avalonia.Templates` | `VeloxDev.Avalonia` | `VeloxDev.Avalonia.WorkflowNodeView` |
| `winui` | `VeloxDev.WinUI.Templates` | `VeloxDev.WinUI` | `VeloxDev.WinUI.WorkflowNodeView` |
| `maui` | `VeloxDev.MAUI.Templates` | `VeloxDev.MAUI` | `VeloxDev.MAUI.WorkflowNodeView` |
| `winforms` | `VeloxDev.WinForms.Templates` | `VeloxDev.WinForms` | `VeloxDev.WinForms.WorkflowNodeView` |
| `razor` | `VeloxDev.Razor.Templates` | `VeloxDev.Razor` | `VeloxDev.Razor.WorkflowNodeView` |
| `jalium` | `VeloxDev.Jalium.Templates` | `VeloxDev.Jalium` | `VeloxDev.Jalium.WorkflowNodeView` |

其余角色把 `NodeView` 换成 `TreeView`、`SlotView`、`LinkView`、`TemplateSelector`、`GridDecorator` 或 `MinimapOverlay`。

## 核对注册

```powershell
dotnet new list winforms-v
```

**预期结果：** 七行，短名与上面 WinForms 列完全一致。同一命令换任一前缀都可用。

### 备注

- `dotnet new list {prefix}-v` 按共同的 `-v` 段过滤；矩阵是完整集合，不是部分列表。
- 文件夹挂载包与 NuGet 包同名同短名会让解析含糊。重复注册时 `dotnet new install` 以非零退出；先卸载。
