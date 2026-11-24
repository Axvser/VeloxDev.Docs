# 过渡动画

过渡按段声明成链。`Execute` 校验链、在目标的调度器上创建 run，并让解释器逐帧采样，直到最后一段结束。

分析分为两个操作：

- [执行链](00_执行链/index.md) — 声明、校验、run 注册、段重放与控制面调用。
- [采样与调度](01_采样与调度/index.md) — 解释器循环、缓动与帧应用、取消与资源。

```csharp
transition.Property(t => t.Opacity, 0d, 1d).AwaitThen(TimeSpan.FromMilliseconds(250));
transition.Execute(target);
```

命名空间：`VeloxDev.TransitionSystem`。
