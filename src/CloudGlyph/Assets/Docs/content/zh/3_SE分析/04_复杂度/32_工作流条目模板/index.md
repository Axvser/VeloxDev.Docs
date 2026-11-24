# 工作流条目模板

一个模板包就是一个 `dotnet new` 条目：每个平台七个角色，七个平台共 49 个条目。生成是一次线性的文件物化加令牌替换 —— 没有条件内容、没有链式模板、没有后置动作。模板自身拥有的运行时复杂度，只有选择器的类型分支。

## 代价模型

| 符号 | 含义 |
|---|---|
| $P$ | 模板包数（7 个平台） |
| $R$ | 每包角色数（7） |
| $F$ | 单个角色发出的文件数（1 或 2） |
| $f_i$ | 条目 $i$ 的文件数 |
| bytes | 发出的文件大小 |

## 条目清单

每个包目录恰好包含七个角色文件夹，每个文件夹一份 `.template.config/template.json`，合计 49 份清单（`Src/Templates/*/working/content/*/.template.config/template.json`）。一个 WPF 节点条目声明自己的标识与一个源名（`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-node-view/.template.config/template.json`）。

```json
"identity": "VeloxDev.WPF.WorkflowNodeView",
"name": "VeloxDev WPF Workflow Node View",
"shortName": "wpf-v-node",
"sourceName": "TemplateClass",
"defaultName": "NodeView",
"preferNameDirectory": false,
"tags": {
  "language": "C#",
  "type": "item"
},
```

七个角色是树、节点、插槽、连线、选择器、装饰器与小地图；短名为 `{prefix}-v-{role}`。视图角色发出一个标记文件加代码隐藏；纯代码角色发一个 `.cs`，但 Razor 的选择器、装饰器与小地图还各带一个 `.razor.cs`。

## 生成代价

生成量与物化文件数成正比，每个文件一次读取、每个声明符号一次令牌替换、一次写入。

$$
T_{\text{new}} = O\left(\sum_{i=1}^{P \cdot R} f_i \cdot (1 + s_i)\right) = O(P \cdot R \cdot F)
$$

49 个包合计发出 80 个文件：六个平台各 11 个，Razor 14 个。没有通配、没有生成器符号、包之间也没有依赖；工作按条目独立，进程层面可并行。

空间是发出文件大小之和 $O(\text{bytes})$，因为 `dotnet new` 先把每个文件渲染进内存再写出。

## 符号替换

每个包声明少量文本参数 —— 命名空间、颜色、线宽 —— 用 `replaces` 字符串标出占位符。替换是对每个文件的每个符号做一次线性替换。WinForms 包多一个参数，因为它的表面背景出现在额外模板里，但渐进形状不变。

49 份清单中没有任何 `condition`、`choice` 或 `value` 符号：平台差异写死在文件内容里，而不是在生成时选择。这保持了生成的线性，也让给定平台与名称时输出确定。

## 生成选择器的运行时代价

选择器模板发出一个 `DataTemplateSelector`，带固定的四臂类型分支（`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-template-selector/TemplateClass.cs:18-31`）。

```csharp
public override DataTemplate SelectTemplate(object item, DependencyObject container)
    => item switch
    {
        ILinkComponent => LinkTemplate
            ?? throw new InvalidOperationException("LinkTemplate is not set."),
        ISlotComponent => SlotTemplate
            ?? throw new InvalidOperationException("SlotTemplate is not set."),
        INodeComponent => NodeTemplate
            ?? throw new InvalidOperationException("NodeTemplate is not set."),
        _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
    };
```

选择是每个条目 $O(1)$，命中路径零分配。一帧实现 $v$ 个条目时花 $O(v)$ 次选择调用，与视图池自身的 $O(v)$ 物化同阶。

## 模板不负责的部分

包内没有视图托管、没有池策略、没有绘制循环；这些来自适配器。生成的视图参与各适配器下的代价分析 —— 128 点曲线、损坏矩形、保留式小地图元素 —— 模板只固定它们的源码形状。这也是模板自身复杂度由文件数量而非图规模主导的原因。

## 相关

- [平台适配器契约](../24_平台适配器契约/index.md) —— 模板实现的那组角色。
- [WPF适配器](../25_WPF适配器/index.md) —— 生成视图的一种具体代价画像。
