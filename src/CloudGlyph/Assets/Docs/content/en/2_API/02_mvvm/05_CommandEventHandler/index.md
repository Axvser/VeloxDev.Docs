# MVVM — `CommandEventHandler`

**Signature** (`VeloxCommand.cs`, line 380):

```csharp
public delegate void CommandEventHandler(CommandEventArgs e);
```

- **Notes:** The payload is a single `CommandEventArgs`, not an `(object sender, CommandEventArgs)` pair — unlike the standard .NET event pattern.
