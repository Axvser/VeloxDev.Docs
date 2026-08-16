# MVVM — `CommandEventType`

**签名**（`VeloxCommand.cs`，第 3-14 行）：

```csharp
public enum CommandEventType : int
{
    None = 0,
    Created,   // created
    Enqueued,  // queued, waiting
    Dequeued,  // dequeued, about to run
    Started,   // actually started
    Completed, // succeeded
    Failed,    // failed
    Canceled,  // canceled
    Exited     // lifecycle ended
}
```
