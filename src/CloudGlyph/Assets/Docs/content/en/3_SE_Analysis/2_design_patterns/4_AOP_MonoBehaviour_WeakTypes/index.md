# Design Patterns — AOP, MonoBehaviour & WeakTypes

## 1. Proxy Pattern (AOP)
Source generator creates a proxy class that wraps method calls with before/after interception.

## 2. Update Method Pattern (MonoBehaviour)
MonoBehaviourManager calls Update(deltaTime) on all registered behaviors each frame.

## 3. Weak Reference Pattern (WeakTypes)
Collections hold WeakReference<T> instead of strong references, allowing GC collection.
