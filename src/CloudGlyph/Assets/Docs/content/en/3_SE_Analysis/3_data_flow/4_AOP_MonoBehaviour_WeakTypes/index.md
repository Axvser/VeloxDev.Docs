# Data Flow — AOP, MonoBehaviour & WeakTypes

## AOP Proxy Flow
Method call -> Proxy intercepts -> Before action -> Original method -> After action -> Return

## MonoBehaviour Frame Loop
MonoBehaviourManager.UpdateAll(deltaTime) -> For each registered behavior -> call Update(dt)
