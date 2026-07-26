# 设计模式 — MVVM

## 1. 命令模式
VeloxCommand 将操作封装为对象，支持 CanExecute/Execute 和事件生命周期。

## 2. 源生成器模式
[VeloxProperty] 和 [VeloxCommand] 属性在编译时触发 Roslyn 生成器。

## 3. 信号量模式
命令通过信号量参数支持可配置的并发限制。
