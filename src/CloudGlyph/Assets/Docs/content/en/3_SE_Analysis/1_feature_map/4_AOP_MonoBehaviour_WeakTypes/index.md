# Feature Map — AOP, MonoBehaviour & WeakTypes

## AOP
- Runtime AOP proxy via Roslyn source generator
- Proxy-to-target reverse lookup (Aop.GetTarget)
- Conditional compilation (#if NET)

## MonoBehaviour
- Unity-style lifecycle: Awake, Start, Update, Destroy
- MonoBehaviourManager: Register, Unregister, frame dispatch
- FrameEventArgs with delta time

## WeakTypes
- WeakCache: Dictionary with weak reference values
- WeakQueue: Queue with weak reference elements
- WeakStack: Stack with weak reference elements
- WeakDelegate: Event handler with weak reference target
