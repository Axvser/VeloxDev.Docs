# 数据流 — 动态主题

## 主题切换流程

1. 用户调用 ThemeManager.Set<T>()
2. 解析新主题类型定义
3. 遍历所有注册的 IThemeObject 实例
4. 对每个属性：读取当前值（StartModel 决定方式）
5. 从新主题定义计算目标值
6. 创建 Transition 快照
7. 通过 TransitionScheduler 执行快照
8. UI 从旧值平滑过渡到新值
