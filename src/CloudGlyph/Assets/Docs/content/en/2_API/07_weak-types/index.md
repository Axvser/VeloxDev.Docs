# Weak Types — API Reference

Namespace `VeloxDev.WeakTypes` ships four weak-reference collection types. Evidence: source (`Src/Core/VeloxDev.Core/WeakTypes/`) and the MSTest suite (`Src/Core/VeloxDev.Core.Test/WeakTypes/`). All four types store `WeakReference<T>` (or a `ConditionalWeakTable`) instead of strong references, so a publisher or cache never roots its subscribers / keys.


## API — Types

This feature's API reference is split by type:

- `00_WeakDelegate/`
- `01_WeakQueue/`
- `02_WeakStack/`
- `03_WeakCache/`
