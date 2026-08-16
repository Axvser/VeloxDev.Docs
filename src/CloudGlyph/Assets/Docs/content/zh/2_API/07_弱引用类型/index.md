# 弱引用类型 — API 参考

命名空间 `VeloxDev.WeakTypes` 提供四个弱引用集合类型。证据来源：源码（`Src/Core/VeloxDev.Core/WeakTypes/`）与 MSTest 测试套件（`Src/Core/VeloxDev.Core.Test/WeakTypes/`）。四个类型都存储 `WeakReference<T>`（或 `ConditionalWeakTable`）而非强引用，因此发布者 / 缓存不会持有订阅者 / 键的强引用。


## API — Types

This feature's API reference is split by type:

- `00_WeakDelegate/`
- `01_WeakQueue/`
- `02_WeakStack/`
- `03_WeakCache/`
