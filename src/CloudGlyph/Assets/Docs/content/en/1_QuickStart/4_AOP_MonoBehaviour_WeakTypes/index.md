# AOP, MonoBehaviour & WeakTypes — Quick Start

## AOP (Aspect Oriented Programming)

VeloxDev AOP provides runtime proxy generation for aspect-oriented programming.

```csharp
using VeloxDev.AspectOriented;

// Mark a class for AOP proxy generation
public partial class MyService : IAspectOriented
{
	public async Task DoWorkAsync()
	{
		// Source generator creates AOP proxy
		// Method calls can be intercepted
	}
}

// Access the original target from proxy
var original = Aop.GetTarget<MyService>(proxy);
```

## MonoBehaviour (Unity-Style Lifecycle)

Unity-style component lifecycle managed by MonoBehaviourManager.

```csharp
using VeloxDev.TimeLine;

[MonoBehaviour]
public class MyBehavior
{
	void Awake() { }           // Called when registered
	void Start() { }           // Called on first frame
	void Update(float dt) { }  // Called every frame
	void Destroy() { }         // Called when unregistered
}

// Managed by MonoBehaviourManager
MonoBehaviourManager.Register(myBehavior);
MonoBehaviourManager.UpdateAll(0.016f); // Called each frame
```

## WeakTypes (Weak Reference Collections)

Collections that hold weak references, allowing garbage collection of entries.

```csharp
using VeloxDev.WeakTypes;

var cache = new WeakCache<string, MyClass>();
cache.Add("key", new MyClass());
if (cache.TryGetValue("key", out var value)) { }

var queue = new WeakQueue<MyClass>();
queue.Enqueue(new MyClass());
if (queue.TryDequeue(out var item)) { }

var stack = new WeakStack<MyClass>();
stack.Push(new MyClass());
if (stack.TryPop(out var item)) { }

var del = new WeakDelegate<EventHandler>();
del += MyHandler;
del?.Invoke(null, EventArgs.Empty);
```
