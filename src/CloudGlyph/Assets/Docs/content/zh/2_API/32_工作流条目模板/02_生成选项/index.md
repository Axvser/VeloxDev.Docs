# 生成选项

每个包接受相同的选项名与别名，命令行因此可以在 GUI 之间原样移动。`template.json` 声明每个符号与默认值；`dotnetcli.host.json` 提供别名。

## 三个结构选项

| 选项 | 长名 | 含义 |
| --- | --- | --- |
| `-n` | `--name` | 类名与文件名。`sourceName` 是 `TemplateClass`，所以它也会重写 `x:Class` 与每一处引用。 |
| `-ns` | `--namespace` | 每个生成文件中的 `TemplateNamespace`。七个必须一致。 |
| `-o` | `--output` | 输出文件夹。`preferNameDirectory` 为 `false`，`-o Views` 直接写进 `Views/`，不建按名子目录。 |

默认类名是 `TreeView`、`NodeView`、`SlotView`、`LinkView`、`TemplateSelector`（WinForms 为 `CustomTemplateSelector`）、`GridDecorator` 与 `MinimapOverlay`。命名空间默认 `MyApp.Views`。

## 样式符号

### 节点视图

| 短 | 长 | 符号 | 默认 |
| --- | --- | --- | --- |
| `-sb` | `surface-background` | `surfaceBackground` | `#FF1E1E1E`（仅 WinForms） |
| `-bg` | `background` | `nodeBackground` | `#DDFFFFFF` |
| `-fg` | `foreground` | `nodeForeground` | `#DD1E1E1E` |
| `-bb` | `border-brush` | `nodeBorderBrush` | `#331E1E1E` |
| `-bt` | `border-thickness` | `nodeBorderThickness` | `1` |
| `-cr` | `corner-radius` | `nodeCornerRadius` | `6` |

### 插槽视图

| 短 | 长 | 符号 | 默认 |
| --- | --- | --- | --- |
| `-bg` | `background` | `slotBackground` | `#01000000` |
| `-sp` | `slot-path` | `slotPath` | SVG 路径数据（惰性，见下） |
| `-sc` | `color` | `slotColor` | `#DD1E1E1E` |
| `-bc` | `border-color` | `slotBorderColor` | `#FFFFFFFF` |

### 连线视图

| 短 | 长 | 符号 | 默认 |
| --- | --- | --- | --- |
| `-lc` | `line-color` | `linkColor` | `#DDFFFFFF` |
| `-lt` | `line-thickness` | `linkThickness` | `2` |

### 树视图

| 短 | 长 | 符号 | 默认 |
| --- | --- | --- | --- |
| `-bg` | `background` | `surfaceBackground` | `#1E1E1E` |
| `-bb` | `border-brush` | `surfaceBorderBrush` | `#33FFFFFF` |
| `-bt` | `border-thickness` | `surfaceBorderThickness` | `1` |
| `-cr` | `corner-radius` | `surfaceCornerRadius` | `3`（WinForms `0`） |

### 网格装饰器

| 短 | 长 | 符号 | 默认 |
| --- | --- | --- | --- |
| `-bg` | `background` | `gridBackground` | `#1E1E1E` |
| `-mic` | `minor-grid-color` | `minorGridColor` | `#2A2D2E` |
| `-mac` | `major-grid-color` | `majorGridColor` | `#3A3D40` |
| `-ac` | `axis-color` | `axisColor` | `#4D4D4D` |
| `-gs` | `grid-spacing` | `gridSpacing` | `40` |
| `-mle` | `major-line-every` | `majorLineEvery` | `5` |
| `-rb` | `ruler-background` | `rulerBackground` | `#C8252526` |
| `-rtc` | `ruler-tick-color` | `rulerTickColor` | `#555555` |
| `-rlc` | `ruler-label-color` | `rulerLabelColor` | `#888888` |
| `-rdc` | `ruler-divider-color` | `rulerDividerColor` | `#3A3D40` |

### 小地图覆盖层

| 短 | 长 | 符号 | 默认 |
| --- | --- | --- | --- |
| `-bg` | `background` | `minimapBackground` | `#331E1E1E` |
| `-bdr` | `border` | `minimapBorder` | `#DC94A3B8` |
| `-nf` | `node-fill` | `nodeFill` | `#DC38BDF8` |
| `-vs` | `viewport-stroke` | `viewportStroke` | `#F0FFFFFF` |

选择器条目没有样式符号；只适用 `-ns`。

## 惰性符号

没有消费者的符号仍会解析，但什么也不改。这些值为了跨 GUI 的命令行一致而存在，并在各包自己的 `template.json` 中注明。

| GUI | 条目 | 惰性符号 |
| --- | --- | --- |
| 每个包 | slot | `slotPath` —— 字形是椭圆或圆 |
| Razor | slot | `slotBackground` |
| Razor | decorator | `gridBackground`、`minorGridColor`、`majorGridColor` |
| Razor | tree | `surfaceBorderBrush`、`surfaceBorderThickness`、`surfaceCornerRadius` |

颜色不出现时，直接改生成文件，不要继续调命令行。

## 示例

```powershell
dotnet new winforms-v-node -n NodeView -ns MyWorkflowApp.Views -o Views `
    -bg "#DD101820" -fg "#FFE5F4FF" -cr 10
```

**预期结果：** `Views/NodeView.xaml` 与 `Views/NodeView.xaml.cs` 带上新颜色与圆角。符号替换也会改写生成注释里出现的同一个值；那只是观感。

### 备注

- 七条命令的 `-ns` 保持一致；树通过它解析兄弟。
- 别名是按条目的，不是全局：`-bg` 在 node 上是 `nodeBackground`，在 tree 上是 `surfaceBackground`，在 minimap 上是 `minimapBackground`。
