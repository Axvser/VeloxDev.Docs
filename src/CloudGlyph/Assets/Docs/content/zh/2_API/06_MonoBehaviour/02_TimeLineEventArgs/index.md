# MonoBehaviour — `TimeLineEventArgs`

```csharp
public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

#### `TimeLineEventArgs.Handled`

**签名：**
`public virtual bool Handled { get; set; }`

**返回：** `bool` — `true` 会短路当前帧阶段剩余的行为调用。

**说明：**
- 默认 `false`（由 `TimeLineEventArgsTests` 验证）。
