# 设计模式 — AOP、MonoBehaviour 与 WeakTypes

## 1. 代理模式 (AOP)
源生成器创建包装方法调用的代理类，支持前置/后置拦截。

## 2. 更新方法模式 (MonoBehaviour)
MonoBehaviourManager 每帧对所有注册行为调用 Update(deltaTime)。

## 3. 弱引用模式 (WeakTypes)
集合持有 WeakReference<T> 而非强引用，允许 GC 回收。
