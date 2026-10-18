# 定义切面目标

声明一个 **`partial` 类**，并标记要拦截的成员。类必须是 `partial`：生成器只考虑 partial 类声明，非 partial 类会被静默跳过。

```csharp
using VeloxDev.AspectOriented;

namespace AopQuickStart;

public partial class Counter
{
    [AspectOriented]
    public int Total { get; set; }

    [AspectOriented]
    public int Add(int a, int b)
    {
        Total = a + b;
        return Total;
    }

    [AspectOriented]
    public void Reset()
    {
        Total = 0;
    }
}
```

## 哪些成员会被镜像

| 声明形式 | 生成条件 | 代理成员 |
|---|---|---|
| 字段 | 带有 `[AspectOriented]` **且**带有简单名含 `Observable` 或 `Property` 的特性（`[VeloxProperty]`、`[Observable]`） | 由字段名推导的 `get`/`set` 属性（`_name` → `Name`） |
| 属性 | 带有 `[AspectOriented]`；存在公有 getter 或未声明 getter 时镜像 getter；仅当存在公有 setter 时镜像 setter | 同名属性 |
| 方法 | 带有 `[AspectOriented]` 且为 `public` | 同名方法，参数与返回类型为全限定名 |

`[AspectOriented]` 必须用简单名书写。生成器按成员上的文本 `AspectOriented` 匹配（`Base/AnalizeHelper.cs`），因此 `[VeloxDev.AspectOriented.AspectOriented]` 与别名形式不会被识别。

## 生成产物

对上面的 `Counter`，生成器产出（均在消费方程序集内）：

| 产物 | 类型 | 文件名提示 |
|---|---|---|
| 接口 | `public interface VeloxDev.AopInterfaces.Counter_AopQuickStart_Aop : IAspectOriented, IAopHookTarget` | `Counter_AopQuickStart_Aop.g.cs` |
| 代理 | `internal sealed class Counter_AopQuickStart_AopProxy : Counter_AopQuickStart_Aop` | `Counter_AopQuickStart_AopProxy.g.cs` |
| 扩展 | `VeloxDev.AspectOriented` 下的 `public static class Counter_AopQuickStart_AopExtensions` | `Counter_AopQuickStart_AopExt.g.cs` |

名称段是所属命名空间把 `.` 替换为 `_` 的结果；全局命名空间中的类使用 `Global`（`Base/AopNames.cs`）。`Counter` 本身不会被注入任何东西 —— 用户类不实现该接口。

## 限制

生成器复制方法名、参数与返回类型，但不复制类型参数列表，且生成的代理按值传递实参。因此被拦截的方法应保持简单：

- 名称唯一 —— 挂钩键就是裸方法名，所以**不支持重载**；
- 不支持 `ref` / `out` / `in` 参数；
- 不支持泛型方法参数。

## 预期结果

`dotnet build` 成功，IntelliSense 中 `counter.Aop()` 解析为返回 `Counter_AopQuickStart_Aop` 的生成扩展方法。
