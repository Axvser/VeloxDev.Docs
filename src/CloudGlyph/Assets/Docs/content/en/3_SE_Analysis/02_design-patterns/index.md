# 02 · Design Patterns

Design-pattern analysis for each feature. Every page below documents the patterns the feature employs — with a Mermaid `classDiagram` showing the interfaces, base classes, and concrete implementations, plus a table describing each pattern and where it appears.

| Feature | Key patterns |
|---|---|
| [00 Workflow System](00_workflow-system) | Command, Template Method, Proxy, Observer, Strategy, Composition, Virtual Proxy, Strategy (runtime redirect) |
| [01 Workflow Agent](01_workflow-agent) | Builder, Facade, Command, Memento, Decorator, Adapter, Observer, Strategy |
| [02 MVVM](02_mvvm) | Command, Observable Property, Source-Generator Template |
| [03 Transition](03_transition) | Fluent Builder + chain, Registry, Strategy (Eases + ISampler), Template Method, Adapter, Scheduler + CWT cache, Composite, Observer |
| [04 Dynamic Theme](04_dynamic-theme) | Facade, Weak Registry, Cache, Virtual seam (`CreateScheduler`), Shared transport (one `TransitionTimeline`), Memoized factory (`FromProperty`), Strategy (`StartModel` + sampler), Template Method (generator), Adapter/Bridge (platform converters) |
| [05 AOP](05_aop) | Proxy, Decorator, Interceptor |
| [06 MonoBehaviour](06_monobehaviour) | Lifecycle Hook / Template Method, Publisher-Subscriber |
| [07 Weak Types](07_weak-types) | Weak Reference, Sweep-on-Access |
| [08 Platform Adapters](08_platform-adapters) | Adapter, Attached Behavior, Object Pool, Command, Strategy / Bridge, Observer |
