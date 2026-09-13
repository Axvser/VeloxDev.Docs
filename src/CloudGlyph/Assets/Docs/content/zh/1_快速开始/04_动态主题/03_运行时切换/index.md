# 动态主题 — 运行时切换

## 运行时切换总览

本页所有内容都发生在 `InitializeTheme()` 已把对象注册进来之后（见[声明与注册](../02_声明与注册/index.md)）。切换是全局的：它会遍历每一个已注册的 `IThemeObject`，移动这些对象声明过的属性。

切换有两种方式，它们的区别不止于观感：

- `ThemeManager.Transition<T>(effect)` 把整场切换当作 TransitionSystem 引擎上的**动画**来跑 —— 属性值由引擎的采样循环逐帧产出，且一场切换的所有目标都锚定在同一条共享时间轴上，因此过渡动画自己的 `Transition.Pause` / `Seek` / `SetRate` / `Exit` 表面能原样驱动一场主题切换。
- `ThemeManager.Jump<T>()` **同步**写入目标值，在调用线程上完成，没有时间轴也没有 effect。它完全不需要平台插值器。

两条路径通知同一组钩子、顺序也相同，并且都会拒绝「切到当前主题」这种空切换。

- [00 准备一场带动画的切换](00_准备/index.md) —— `SetPlatformInterpolator`（带动画时的强制项）、`StartModel`、effect 预设
- [01 带动画与即时切换](01_带动画与即时切换/index.md) —— `Transition` / `Jump`、生成的钩子、`SetCurrent`
- [02 控制运行中的切换](02_控制切换/index.md) —— 一场切换一条时间轴，`Pause` / `Resume` / `Seek` / `SetRate` / `Exit`
- [03 运行时覆盖与线程](03_运行时覆盖与线程/index.md) —— `SetThemeValue` / `RestoreThemeValue`、两个缓存、切换写在哪个线程上
