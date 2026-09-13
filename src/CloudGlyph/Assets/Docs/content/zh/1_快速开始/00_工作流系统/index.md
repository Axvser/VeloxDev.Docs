# 工作流系统 — 快速开始

VeloxDev 工作流系统是一个与 UI 框架无关的**可视化工作流编辑引擎**。你用四类组件 —— **Tree（树/画布）**、**Node（节点）**、**Slot（槽位）**、**Link（连接线）** —— 搭出有向无环图，再用**编译器**把它变成一段可执行计划（`CompiledGraph`），交给**运行时引擎**驱动。`[WorkflowBuilder.*]` 属性 + Roslyn 源生成器负责生成全部 ViewModel 样板（属性、Helper、命令、撤销/重做、初始化）；引擎本身不依赖任何 GUI 框架，适配器（WPF / Avalonia / WinUI / MAUI / WinForms / Razor）只负责把图画出来。

本指南用一个**单控制台程序**带你跑通一条完整的“编译 → 运行”链路。示例图是一条扇出计算链：

```text
seed(2.0) ──► Source ──┬──► Report ──►（打印结果）
   (倍乘×2, 扇出)       └──► Discard  ──►（兄弟支，用于观察剪枝）
```

- **正向编译**（`CompileRole.Root`）：从 `Source` 向下游把可达子图分解成 `[ChainSegment, ParallelSegment]`，`RuntimeEngine` 沿图驱动每个节点。
- **反向/终端编译**（`CompileRole.Terminal`）：只编译能算出 `Report` 值的那部分祖先锥 —— `Discard` 支不在锥内，因此既不被编译也不被驱动。
- 最后把整棵树 `Serialize()` 成 JSON，再 `Deserialize<T>()` 重建并重跑。

每一步都给出**可观测预期结果**；代码为真实源码、可编译、无省略号。结尾 `07 完整代码` 页给出**单一最小可运行程序**及**运行声明**。

> 跨维度一致性：本功能在 `2_API` 与 `3_SE分析` 中同名目录是 `00_工作流系统`。

## 子页面

- [00 前置条件](00_前置条件/index.md) — 支持目标 / SDK / 包管理器 / 运行环境
- [01 安装 / 添加依赖](01_安装/index.md) — 引入 `VeloxDev.Core` 与源生成器
- [02 定义组件](02_定义组件/index.md) — Tree / Slot / Node 类与节点 Helper
- [03 构建画布](03_构建画布/index.md) — 建树、注册节点、配通道、连线
- [04 编译与正向运行](04_编译与运行/index.md) — `CompileRole.Root` 编译 + `RuntimeEngine` 运行
- [05 终端结果编译](05_终端编译/index.md) — `CompileRole.Terminal` 反向锥 + `Target` 追踪
- [06 序列化](06_序列化/index.md) — 整棵树 JSON 往返
- [07 验证与完整代码](07_完整代码/index.md) — 对照 Demo / 测试 + 完整程序 + 运行声明
