# 平台适配器 — 验证

## 1. 需要检查的可观测结果

宿主好生成的视图（见「配置」与「核心用法」）后，逐一确认每个行为：

| 操作 | 可观测结果 |
|---|---|
| 拖拽空白背景 | 画布平移；网格/标尺与小地图跟随滚动偏移。 |
| 在画布上 Ctrl + 鼠标滚轮 | 围绕视口中心缩放；小地图里的视口指示框同步更新。 |
| 拖拽节点头部 | 节点跟随光标移动；输入/输出槽锚点随之更新。 |
| 按下输出槽，把指针移到输入槽上，再松开 | 移动过程中候选槽显示 `PreviewReceiver`，虚拟连线报告 `ValidTarget`（Core 会拒绝的槽则为 `InvalidTarget`）；在有效槽上松开创建连线；槽针脚按 `SlotState` 换色。 |
| 滚得很远 / 添加很多节点 | 只有可见的项视图被实例化（虚拟化）——可见项计数器保持有界。 |
| 在小地图里拖拽 | 画布滚动到小地图指示的位置。 |

## 2. 运行仓库内演示

最完整的参考实现是 WPF 演示：

```powershell
dotnet run --project Examples/Workflow/WPF/Demo
```

打开左侧面板里的工作流树（「Load Workflow Demo」），然后对比**节点总数**与**可见组件数**两个计数器：无论树多大，后者都保持很小——这证实了 `ViewPool` 的虚拟化。每个平台在 `Examples/Workflow/<平台>` 下都有对应的演示（各自带 `Trimmed` 变体）；`Examples/Transition/*` 与 `Examples/Theme/*` 下的过渡/主题演示展示适配器的过渡/主题接线。

## 运行声明

- ⚠️ **本次修订（2026-10-18）没有构建或运行。** 本页所有论断均依据适配器源码（`Src/Adapters/*`）、Core 的输入/预览路径（`Src/Core/VeloxDev.Core/WorkflowSystem`）与演示调用形态（`Examples/Workflow/WPF/Demo`、`Examples/Transition/WPF`、`Examples/Theme/WPF`）静态核验。未启动 GUI，因此平移 / 缩放 / 拖拽 / 连接预览 / 小地图均未在屏幕上观察。
- ✅ 历史记录（2026-10-01，本次未重跑）：`dotnet build Examples/Workflow/WPF/Demo/Demo.csproj`（Debug，`net9.0-windows`）把 WPF 适配器及其工作流行为针对 Core 引擎编译通过，**0 警告 / 0 错误**：

```text
  VeloxDev.WPF -> ...\Src\Adapters\VeloxDev.WPF\bin\Debug\net5.0-windows\VeloxDev.WPF.dll
  Demo -> ...\Examples\Workflow\WPF\Demo\bin\Debug\net9.0-windows\Demo.dll

已成功生成。
    0 个警告
    0 个错误
```
