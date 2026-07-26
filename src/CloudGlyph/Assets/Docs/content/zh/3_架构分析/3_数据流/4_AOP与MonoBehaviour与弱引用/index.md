# 数据流 — AOP、MonoBehaviour 与 WeakTypes

## AOP 代理流程
方法调用 -> 代理拦截 -> 前置操作 -> 原始方法 -> 后置操作 -> 返回

## MonoBehaviour 帧循环
MonoBehaviourManager.UpdateAll(dt) -> 遍历所有行为 -> 调用 Update(dt)
