# 动态主题 — API 参考

## 命名空间：`VeloxDev.DynamicTheme`

### ThemeManager

| 成员 | 描述 |
|---|---|
| `Current` | 当前主题类型（默认：Dark） |
| `StartModel` | 初始值获取方式：Reflect 或 Cache |
| `SetPlatformInterpolator<T>(T)` | 注册平台插值器 |
| `SetCurrent<T>()` | 无动画切换主题 |
| `Set<T>(bool smooth = true)` | 带动画切换主题 |
| `Register(IThemeObject)` | 注册主题元素 |
| `Unregister(IThemeObject)` | 注销主题元素 |

### 接口

| 接口 | 用途 |
|---|---|
| `ITheme` | 主题定义契约 |
| `IThemeObject` | 使元素支持主题 |
| `IThemeValueConverter` | 主题值到平台类型的转换 |

### 关键类型

| 类型 | 描述 |
|---|---|
| `Dark`, `Light` | 内置主题定义 |
| `ThemeCache` | 管理缓存的主题属性值 |
