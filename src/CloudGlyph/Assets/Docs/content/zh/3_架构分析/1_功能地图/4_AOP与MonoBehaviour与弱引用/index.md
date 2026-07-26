# 功能地图 — AOP、MonoBehaviour 与 WeakTypes

## AOP
- 通过 Roslyn 源生成器实现运行时 AOP 代理
- 代理到目标的逆向查找 (Aop.GetTarget)

## MonoBehaviour
- Unity 风格生命周期: Awake, Start, Update, Destroy
- MonoBehaviourManager 管理注册和帧调度

## WeakTypes
- WeakCache: 弱引用字典
- WeakQueue: 弱引用队列
- WeakStack: 弱引用栈
- WeakDelegate: 弱引用事件处理
