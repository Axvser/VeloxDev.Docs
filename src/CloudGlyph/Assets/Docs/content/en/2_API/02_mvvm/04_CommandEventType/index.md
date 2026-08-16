# MVVM — `CommandEventType`

**Signature** (`VeloxCommand.cs`, lines 3-14):

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
