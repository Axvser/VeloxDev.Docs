# AOP, MonoBehaviour & WeakTypes — API Reference

## AOP (`VeloxDev.AspectOriented`)

| Type | Description |
|---|---|
| `Aop` | Static proxy-to-target reverse lookup |
| `IAspectOriented` | Marks a class for AOP proxy generation |
| `AspectOrientedAttribute` | Marks methods for interception |

## MonoBehaviour (`VeloxDev.TimeLine`)

| Type | Description |
|---|---|
| `MonoBehaviourAttribute` | Marks a class as MonoBehaviour |
| `MonoBehaviourManager` | Manages lifecycle registration and frame dispatch |
| `FrameEventArgs` | Frame update event data with delta time |
| `TimeLineEventArgs` | Timeline event data |

## WeakTypes (`VeloxDev.WeakTypes`)

| Type | Description |
|---|---|
| `WeakCache<TKey, TValue>` | Weak reference dictionary |
| `WeakQueue<T>` | Weak reference queue |
| `WeakStack<T>` | Weak reference stack |
| `WeakDelegate<T>` | Weak event handler delegate |
