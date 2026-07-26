# 复杂度分析 — 工作流系统

## 类层次结构复杂度

```
IWorkflowViewModel（基类）
├── IWorkflowTreeViewModel    ← 10 个属性, 8 个命令
├── IWorkflowNodeViewModel    ← 5 个属性, 9 个命令
├── IWorkflowSlotViewModel    ← 6 个属性, 5 个命令
└── IWorkflowLinkViewModel    ← 4 个属性

Helper 层次结构：
IWorkflowHelper（基类）
├── IWorkflowTreeViewModelHelper  ← +事件, Install/Uninstall, CreateNode/Link
├── IWorkflowNodeViewModelHelper  ← +事件, WorkAsync, ValidateBroadcastAsync
├── IWorkflowSlotViewModelHelper  ← +事件
└── IWorkflowLinkViewModelHelper  ← +事件

实现层次结构：
TreeHelper<T>         → IWorkflowTreeViewModelHelper（默认：约 200 行）
NodeHelper<T>         → IWorkflowNodeViewModelHelper（默认：约 80 行）
SlotHelper<T>         → IWorkflowSlotViewModelHelper（默认：约 50 行）
LinkHelper<T>         → IWorkflowLinkViewModelHelper（默认：约 30 行）
```

## 空间网格复杂度

| 操作 | 时间 | 空间 | 说明 |
|---|---|---|---|
| `Insert` | O(1) | O(n) | 基于哈希的单元插入 |
| `Remove` | O(1) | O(1) | 基于哈希的单元移除 |
| `Query` | O(k + m) | O(1) | k = 视口中单元数, m = 范围内项目数 |
| `Update` | O(2) | O(1) | 移除 + 重新插入 |
| `Global Bounds` | O(1) | O(1) | 增量维护 |

- **网格单元大小**: 可配置（默认 200px）。较小的单元 = 较少的误报但更多内存。
- **最坏情况**: 所有项目在同一个单元中 → 查询降级为 O(n)。

## 工作流编译复杂度

`WorkflowCompiler` 从节点/连接线结构构建有向执行图：

```
输入: N 个节点, L 条连接线
步骤 1: 拓扑排序 → O(N + L)
步骤 2: 组件分析 → O(N + L)（处理不连通子图）
步骤 3: 循环检测 → O(N + L)（Tarjan 或基于 DFS）
步骤 4: 执行计划生成 → O(N + L)

总计: O(N + L) 时间, O(N + L) 空间
```

**循环处理策略**:
- `Error`: 编译失败并报告循环错误
- `SkipCyclic`: 仅执行无环子集
- `Ordered`: 回退到插入顺序

## 代码规模统计（近似值）

| 组件 | 源文件数 | 代码行数 |
|---|---|---|
| 核心接口 | 12 | ~600 |
| 核心实现（`WorkflowSystem/`） | 30 | ~3,500 |
| 模板/ViewModel | 6 | ~1,200 |
| 编译管道 | 15 | ~2,500 |
| 空间索引 | 4 | ~500 |
| 选择器扩展 | 4 | ~400 |
| 标准扩展 | 6 | ~800 |
| 测试 | 8 | ~4,000+ |
| **小计（工作流系统）** | **约 85** | **约 13,500** |

## 依赖图复杂度

```
外部依赖: 无（核心模块零依赖）
内部依赖:
  VeloxDev.Core（自身）
  └── VeloxDev.Core.Generator（源代码生成，仅编译时）

适配器依赖:
  VeloxDev.WorkflowSystem（核心）
  └── VeloxDev.WPF / Avalonia / WinUI / MAUI（附加行为 + 平台适配器）
```

核心工作流系统具有**零外部 NuGet 依赖**，使其在所有目标框架上轻量且可移植。
