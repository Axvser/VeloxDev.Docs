# 平台适配器 — 验证

## 1. 需要检查的可观测结果

宿主好生成的视图（见「配置」与「核心用法」）后，逐一确认每个行为：

| 操作 | 可观测结果 |
|---|---|
| 拖拽空白背景 | 画布平移；网格/标尺与小地图跟随滚动偏移。 |
| 在画布上 Ctrl + 鼠标滚轮 | 围绕视口中心缩放；小地图里的视口指示框同步更新。 |
| 拖拽节点头部 | 节点跟随光标移动；输入/输出槽锚点随之更新。 |
| 按下输出槽并在输入槽上松开 | 创建一条连线；槽针脚按 `SlotState` 换色。 |
| 滚得很远 / 添加很多节点 | 只有可见的项视图被实例化（虚拟化）——可见项计数器保持有界。 |
| 在小地图里拖拽 | 画布滚动到小地图指示的位置。 |

## 2. 运行仓库内演示

最完整的参考实现是 WPF 演示：

```powershell
dotnet run --project Examples/Workflow/WPF/Demo
```

打开左侧面板里的工作流树（「Load Workflow Demo」），然后对比**节点总数**与**可见组件数**两个计数器：无论树多大，后者都保持很小——这证实了 `ViewPool` 的虚拟化。每个平台在 `Examples/Workflow/<平台>` 下都有对应的演示（各自带 `Trimmed` 变体）；`Examples/Transition/*` 与 `Examples/Theme/*` 下的过渡/主题演示展示适配器的过渡/主题接线。

## 运行声明

- ⚠️ 本环境未实际运行——页面内容对照适配器与模板源码（`Src/Adapters/*`、`Src/Templates/*`）以及演示调用形态（`Examples/Workflow/WPF/Demo`、`Examples/Transition/WPF`、`Examples/Theme/WPF`）做了静态核验，此处没有启动任何 GUI。
