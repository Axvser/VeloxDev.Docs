# 面向切面编程

`VeloxDev.AspectOriented` 在属性 getter、属性 setter 或方法周围提供前置 / 替换 / 后置钩子。生成器产出镜像接口与编译期代理，运行期不做任何代码生成。运行期部分仅在定义 `NET` 符号时编译，因此使用方必须面向 **.NET 5.0 或更高**（`netstandard2.0` 与 `netframework4.6.1` 不包含该命名空间）。

## 类型分组

| 分组 | 类型 | 页面 |
|---|---|---|
| 生成的代理表面 | `AspectOrientedAttribute`、`IAspectOriented`、生成的接口 / 代理 / `Aop()` 扩展、`AopCache`、`Aop` | [生成代理表面](00_生成代理表面/index.md) |
| 钩子与安装 | `ProxyHandler`、`AspectHooks`、`IAopHookTarget`、`ProxyMembers`、`ProxyEx` | [钩子与安装](01_钩子与安装/index.md) |

## 调用如何流转

1. 在公开属性或方法（或 `[VeloxProperty]` 字段）上加 `[AspectOriented]`，生成器产出镜像接口与实现它的代理。
2. `counter.Aop()` 返回缓存的代理。代理上的调用运行已安装钩子；原对象上的调用绕过它们。
3. `proxy.SetProxy(memberKind, memberName, start, coverage, end)` 安装一个成员的三个阶段。再次安装会整体替换三阶段。
4. getter 的处理器 `parameters` 为 `null`；setter 的单个元素是被写入的值；方法的是该方法自身参数。

完整控制台程序见[面向切面编程快速开始](../../1_快速开始/14_面向切面编程/index.md)。

## 限制

- 重载方法无法挂钩：拦截键是裸方法名。
- 需要公开属性；非公开属性或方法不会被织入。
- `[VeloxProperty]` 字段必须与 `[AspectOriented]` 同时存在，被拦截的成员是生成的属性（`_name` 变成 `Name`）。
