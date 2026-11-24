# 定制生成的视图

生成文件是默认值，不是固定件。按你的节点类型、菜单与选择规则直接改它们。

## 样式参数

每个包接受同一套选项名与别名，因此命令行可在 GUI 之间原样搬。别名在各条目的 `.template.config/dotnetcli.host.json` 里；`template.json` 声明符号与默认值。`template.json` 里有 `type: parameter` 却没有 `replaces` 的符号会被 CLI 收下但什么也不替换；七个包为跨 GUI 命令行一致性刻意保留了几个空转符号，并在自己的 `template.json` 里写明（见下面的惰性值表）。

| 条目 | 选项（短 → 符号） | 含义 |
| --- | --- | --- |
| node | `-bg` `nodeBackground` | 卡片填充 |
| node | `-fg` `nodeForeground` | 卡片文字与字形颜色 |
| node | `-bb` `nodeBorderBrush` | 卡片边框 |
| node | `-bt` `nodeBorderThickness` | 卡片边框宽度 |
| node | `-cr` `nodeCornerRadius` | 卡片圆角 |
| slot | `-sc` `slotColor` | 字形填充 |
| slot | `-bc` `slotBorderColor` | 字形描边 |
| link | `-lc` `linkColor` | 静止连线描边 |
| link | `-lt` `linkThickness` | 静止连线宽度 |
| tree | `-bg` `surfaceBackground` | 表面填充 |
| tree | `-bb` `surfaceBorderBrush` | 表面边框 |
| tree | `-bt` `surfaceBorderThickness` | 表面边框宽度 |
| tree | `-cr` `surfaceCornerRadius` | 表面圆角 |
| decorator | `-gs` `gridSpacing` | 网格线间距 |
| decorator | `-mle` `majorLineEvery` | 多少条细线成一条粗线 |
| decorator | `-rb` `rulerBackground` | 标尺带填充 |
| decorator | `-rtc` `rulerTickColor` | 标尺刻度 |
| decorator | `-rlc` `rulerLabelColor` | 标尺标签 |
| minimap | `-bg` `minimapBackground` | 缩略图背景 |
| minimap | `-nf` `nodeFill` | 节点标记填充 |
| minimap | `-vs` `viewportStroke` | 视口指示框描边 |

某个颜色符号在特定 GUI 上可能没有消费者。那些包仍为跨 GUI 命令行一致性声明该符号，并在自己的 `template.json` 里写明；命令行保持统一，生成文件记录这个惰性值。已知的惰性值：

| GUI | 条目 | 惰性符号 |
| --- | --- | --- |
| 所有包 | slot | `slotPath` —— 字形统一画成椭圆或圆 |
| Razor | slot | `slotBackground` |
| Razor | decorator | `gridBackground`、`minorGridColor`、`majorGridColor` |
| Razor | tree | `surfaceBorderBrush`、`surfaceBorderThickness`、`surfaceCornerRadius` |

颜色不出现时，直接改生成文件，而不是反复调命令行。符号替换也会改写生成文件注释里的同一段文字；那只是外观。

## 选择器

VeloxDev 自己的选择器（`ViewPool.TemplateSelector` / `ViewSourcePipeline`）优先级最高：命中就用，平台自带的模板查找只是兜底。

- WinForms 派生 `Easel.Visuals.VisualTemplateSelector`，返回视觉 `NodeView` / `SlotView` / `LinkView`。那家的池没有平台兜底，选择器是唯一创建路径。
- Jalium 派生 `DataTemplateSelector`；默认选择器不设 `SlotTemplate` 与 `TreeTemplate`，而这些条目类型不会进池。
- Razor 的“选择器”是一个包住 `ViewPool` 的组件（`TemplateSelector`），不存在选择器实例。

生成的树已经接好选择器资源。选择器决定某个 ViewModel 用哪个视图；把这条判断留在选择器里，不要在树里写分支。

## 连线菜单

树声明并接好菜单，但**条目是空的** —— 右键会打开一个没有 Delete 的菜单，直到你加条目。

| GUI | 条目写在哪 |
| --- | --- |
| WPF / Avalonia / WinUI / MAUI / Jalium | 由 `WorkflowSurfaceBehavior.LinkMenuKey` 指名的资源（`ContextMenu` / `MenuFlyout`）；每个条目写 `Command="{Binding DeleteCommand}"` |
| WinForms | 树的 `VisualContextMenu x:Key="LinkContextMenu"`，或宿主的 `WorkflowSurfaceBehavior.SetLinkMenuBuilder(this, …)` |
| Razor | 树的 `<LinkMenu Context="link">` 片段；每个条目用内联 `@onclick` |

每个条目都会收到被右键的那条连线，所以一行就是一个完整动作。菜单由适配器定位，打开时还会暂停输入路由。

## 节点内容与端口

- 把内容放在设计尺寸网格上（XAML 平台、WinForms 与 Jalium 是 `260 × 180`；Razor 是 CSS transform）。容器负责缩放；不要把内层网格绑到塌缩后的 `Size`。
- 卡片显示的端口必须被命名。改标记里的 `PART_*` 时，同时改槽布局属性里的名字；没有代码枚举 `node.Slots`。
- 保留 wrapper：外层 `WorkflowSlotLayoutBehavior`，标题条上的 `WorkflowNodeDragBehavior`。Razor 里 `SlotView` 自己已经打开 `WorkflowSlotConnectionBehavior` —— 再包一层会把测量与手势都翻倍。
- 槽颜色是模板固定色。模板不读 `ISlotComponent.State`；要按状态改外观，在宿主里订 `PropertyChanged`。

## 会让复制失效的跨包差异

- **连线策略。** MAUI 把所有连线画在一个视口级 overlay 里；WinForms 与 XAML 包每条连线一个视图。跨这条边界复制连线视图，会得到“构建通过、画布上没有线”。
- **标尺厚度。** 包默认 28，Jalium 是 36。从装饰器读 `RulerBand`，并让画布平移、网格数学与虚拟化 inset 都用这个值。
- **Avalonia 的占位类型。** 生成树里的 `vm:TreeViewModel` 是你的类型，不是生成类型。填对之前构建失败是刻意的：明确报错好过画布静默空白。
- **调试 HUD 不在任何包里。** demo 带 `InfoOverlay`；需要就自己加。

**预期结果：** 改样式后，`dotnet new` 在生成文件里产出新值；改菜单或选择器后，重新构建的应用表现出新行为。
