# AOP 运行时 — `AspectOrientedAttribute` 与 `IAspectOriented`

## 类型：`AspectOrientedAttribute`

声明于 `Src/Core/VeloxDev.Core/AspectOriented/AspectOrientedAttribute.cs`：

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
    AllowMultiple = false, Inherited = false)]
public class AspectOrientedAttribute : Attribute
{
}
```

### 构造函数：`AspectOrientedAttribute`

**签名：** `AspectOrientedAttribute()`

无参数、无状态。

**异常：** 无。

### 语义

- **目标：** 仅方法、属性、字段。
- **识别是文本匹配：** `AnalizeHelper.IsAopClass` 匹配特性的简单名 `AspectOriented`，`AopSurface` 逐成员比较 `att.ToString() == "AspectOriented"`。请写不带限定名的 `[AspectOriented]`。
- **类必须是 `partial`：** 发现过滤器只接受 partial 类声明（`Analizer.Filters.IsCandidateClass`）。非 partial 类会被静默跳过。
- **一个成员被标记，整个类就成为目标。** 所有 partial 声明中的被标记成员都会被收集（`AnalizeHelper.Members`）。
- **暴露规则：** 方法须为 `public`；属性至少有一个公有访问器；字段只有在同时带有属性生成特性（`[VeloxProperty]`、`[Observable]`）时才出现。详见 [生成器产物](../../01_生成的API/index.md)。

Demo 中的标记，`Examples/AOP/WPF/Demo/TeamViewModel.cs`：

```csharp
public partial class TeamViewModel
{
    [VeloxProperty][AspectOriented] private string _name = string.Empty;
    [VeloxProperty][AspectOriented] private ObservableCollection<MemberViewModel> _members = [];

    [AspectOriented]
    public void Reset()
    {
        Name = string.Empty;
        Members.Clear();
    }
}
```

两个字段以 `Name` 与 `Members` 属性出现；`Reset` 以方法出现。

## 类型：`IAspectOriented`

声明于 `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`：

```csharp
public interface IAspectOriented
{
}
```

空标记接口。它的作用：

- **基契约：** 每个生成的 AOP 接口都继承它。
- **约束：** 用于 `ProxyEx.SetProxy<T>` 与 `AopCache.Resolve<TClass, TInterface>`。
- **形参类型：** `Aop.GetTarget<TTarget>` 的形参（其自身约束是 `TTarget : class`）。

生成的接口还继承 `IAopHookTarget`，而后者带有成员；因此用户自己的类**不**实现这两个接口 —— 实现它们的是代理类。参见 [生成的代理](../03_生成的代理/index.md)。
