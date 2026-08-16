# AOP — 生成器产物（源生成器）

由 `AopInterface` / `AopProxy`（`Src/Generators/VeloxDev.Core.Generator`）在编译期生成。具体名字取决于类名及其所在命名空间。

### 类型：`VeloxDev.AopInterfaces.{ClassName}_{Namespace}_Aop`

**签名：** `public interface {ClassName}_{Namespace}_Aop : IAspectOriented` —— 例如 `Demo.TeamViewModel` 生成 `TeamViewModel_Demo_Aop`。

**成员：** 为类的每个可拦截 `[AspectOriented]` 成员生成一个公有成员声明：
- 被 `[VeloxProperty]` / `[Observable]` 标记的字段 → 一个 get/set 属性；
- 公有的 `[AspectOriented]` 属性 → 一个 get/set 属性（只在原访问器为公有时保留相应访问器）；
- 公有的 `[AspectOriented]` 方法 → 一个带全限定参数 / 返回类型的方法。

**备注：** `DispatchProxy.Create<T, ProxyInstance>()` 代理的就是这个接口，因此运行时能按 `get_*` / `set_*` / 普通方法名拦截。

### 扩展方法：`Aop(this T instance)`

**签名：** `public static {ClassName}_{Namespace}_Aop Aop(this T instance)`（命名空间 `VeloxDev.AspectOriented`）—— 例如 `public static TeamViewModel_Demo_Aop Aop(this TeamViewModel instance)`。

| 参数 | 类型 | 说明 |
|---|---|---|
| `instance` | `T` | 目标实例 |

**返回：** `{ClassName}_{Namespace}_Aop` — 缓存（或新建）的代理。

**示例：**
```text
// 出处：Examples/AOP/WPF/Demo/MainWindow.xaml.cs
var team = _teamData.Aop();        // 缓存的代理
_ = _teamData.Aop().Name;          // getter 被拦截
_teamData.Aop().Reset();           // 方法被拦截
```

**备注：**
- 通过 `AopCache.Resolve<T, I>` 解析代理（每对类型一张弱表）。
- 传给 `Resolve` 的工厂调用 `ProxyEx.CreateProxy<I>(x)` 与 `Aop.Map(p, x)`。
- 生成的扩展类名为 `{ClassName}_{Namespace}_AopExtensions`（例如 `TeamViewModel_Demo_AopExtensions`）；为 `public static`。
