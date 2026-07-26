# 功能地图 — 动态主题

## 功能

1. **主题定义** — 实现 ITheme 的类定义调色板和常量
2. **元素注册** — IThemeObject 元素注册到 ThemeManager
3. **动画切换** — 主题变更使用 TransitionSystem 实现平滑动画
4. **值转换** — IThemeValueConverter 适配到平台特定类型
5. **缓存** — 通过 StartModel.Cache 实现值的缓存
