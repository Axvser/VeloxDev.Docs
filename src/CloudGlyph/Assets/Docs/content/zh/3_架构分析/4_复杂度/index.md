# 复杂度分析

VeloxDev 各模块的时间与空间复杂度分析。

| 模块 | 描述 |
|---|---|
| [工作流系统](0_工作流系统) | O(N+L) 编译、O(1) 空间操作 |
| [过渡动画系统](1_过渡动画系统) | O(1) 注册表、O(steps) 插值 |
| [动态主题](2_动态主题) | O(N*P) 主题切换 |
| [MVVM](3_MVVM) | O(1) 命令分发 |
| [AOP、MonoBehaviour 与 WeakTypes](4_AOP与MonoBehaviour与弱引用) | O(1) 代理分发 |
