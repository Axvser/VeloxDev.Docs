# AOP、MonoBehaviour 与弱引用 — 快速入门

## AOP (面向切面编程)

`csharp
using VeloxDev.AspectOriented;

public partial class MyService : IAspectOriented
{
	public async Task DoWorkAsync() { }
}

var original = Aop.GetTarget<MyService>(proxy);
`

## MonoBehaviour (Unity 风格生命周期)

`csharp
using VeloxDev.TimeLine;

[MonoBehaviour]
public class MyBehavior
{
	void Awake() { }
	void Start() { }
	void Update(float deltaTime) { }
	void Destroy() { }
}

MonoBehaviourManager.Register(myBehavior);
`

## WeakTypes (弱引用集合)

`csharp
using VeloxDev.WeakTypes;

var cache = new WeakCache<string, MyClass>();
var queue = new WeakQueue<MyClass>();
var stack = new WeakStack<MyClass>();
var del = new WeakDelegate<EventHandler>();
`
