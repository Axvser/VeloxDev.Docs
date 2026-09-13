# AOP 运行时 — `AspectOrientedAttribute` 与 `IAspectOriented`

AOP 功能的声明面：`AspectOrientedAttribute` 标记某个 `partial` 类中应经由动态代理暴露的成员；`IAspectOriented` 是所有生成 AOP 接口继承的空标记契约。

## 类型：`AspectOrientedAttribute`

`Src/Core/VeloxDev.Core/AspectOriented/AspectOrientedAttribute.cs`：

```csharp
namespace VeloxDev.AspectOriented
{
    [AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
        AllowMultiple = false, Inherited = false)]
    public class AspectOrientedAttribute : Attribute
    {
    }
}
```

### 构造函数：`AspectOrientedAttribute`

**签名：** `AspectOrientedAttribute()`

| 参数 | 类型 | 说明 |
|---|---|---|
| （无） | | 无参构造函数（该特性不携带任何状态） |

**返回：** `AspectOrientedAttribute`

**异常：** 无。

### 特性语义

- **目标：** 仅 `Method`、`Property`、`Field`；`AllowMultiple = false`，`Inherited = false`。
- **识别：** 生成器按特性简单名 `AspectOriented` 匹配（`Base/AnalizeHelper.IsAopClass`、`Writers/AopWriter.ReadAopConfig`）。只要类中一个成员带有该特性，整个包含它的 `partial` 类就成为 AOP 目标，生成器随之产出其 AOP 接口、partial 类胶水与 `Aop(this T)` 扩展（见 [生成器产物](../../01_生成的API/index.md)）。
- **暴露：** 生成器放到代理接口上的成员必须是 `public`（私有字段只有在 `[VeloxProperty]` / `[Observable]` 生成器将其变成公有属性后才会上接口）。

Demo 验证的标记，`Examples/AOP/WPF/Demo/TeamViewModel.cs`：

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

此处两个字段同时带有 `[VeloxProperty]`（MVVM），因此以 `Name` 与 `Members` 属性形式出现在代理接口上；两个 `[AspectOriented]` 公有方法（`Reset`，以及文件后面出现的 `AOP_OnMemberAdded` / `AOP_OnMemberRemoved`）被直接暴露。

## 类型：`IAspectOriented`

`Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`：

```csharp
namespace VeloxDev.AspectOriented
{
    public interface IAspectOriented
    {
    }
}
```

无任何成员的空标记接口。它的作用：

- **作为所有生成 AOP 接口的基契约** —— 生成器写入基类型 `global::VeloxDev.AspectOriented.IAspectOriented`。
- **作为公共泛型约束** —— 被 `ProxyEx.CreateProxy<T>`、`ProxyEx.SetProxy<T>`、`Aop.GetTarget<TTarget>` 与 `AopCache.Resolve<TClass, TInterface>` 共同使用（见 [proxyex](../02_proxyex/index.md) 与 [代理生命周期](../04_代理生命周期/index.md)）。

相关页面：[ProxyMembers 与 ProxyHandler](../01_代理成员处理器/index.md)、[ProxyEx](../02_proxyex/index.md)、[ProxyInstance](../03_proxyinstance/index.md)。
