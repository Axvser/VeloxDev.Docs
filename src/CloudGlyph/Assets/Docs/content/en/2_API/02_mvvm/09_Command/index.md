# MVVM — `Command`

Reads `VeloxCommandAttribute` from methods (`CommandWriter.ReadCommandConfig`, lines 19-77), resolves `name` / `canValidate` / `semaphore` (positional then named arguments), applies the `Async`-suffix strip, selects the factory via `ParseConstructorType` (lines 78-116), and emits a lazy `IVeloxCommand` property per method.
