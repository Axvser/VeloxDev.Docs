# MVVM — `Command`

从方法读取 `VeloxCommandAttribute`（`CommandWriter.ReadCommandConfig`，第 19-77 行），解析 `name` / `canValidate` / `semaphore`（先位置参数后命名参数），应用 `Async` 后缀剥离，通过 `ParseConstructorType`（第 78-116 行）选择工厂，并为每个方法生成一个懒加载的 `IVeloxCommand` 属性。
