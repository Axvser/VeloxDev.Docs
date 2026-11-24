# Closed-world serialization

`VeloxJsonSerializer` writes and reads the archive format through a registry compiled over a closed type set. A value is written by the writer its runtime type registered and read by the reader the document's `$type` names. There is no reflection fallback.

The analysis splits into two operations:

- [Write path](00_write-path/index.md) — `Serialize`, `WriteValue`, scalar/container dispatch and registry lookup.
- [Read path](01_read-path/index.md) — `Deserialize`, `ReadValue`, reference registration and generated readers.

```csharp
var json = workflow.Serialize();
var restored = json.Deserialize<MyViewModel>();
```

Namespace: `VeloxDev.Serialization`.
