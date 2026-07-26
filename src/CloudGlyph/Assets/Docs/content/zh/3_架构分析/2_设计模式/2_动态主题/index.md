# 设计模式 — 动态主题

## 观察者模式
ThemeManager 在主题变更时通知所有注册的 IThemeObject 实例。

## 策略模式
StartModel (Reflect/Cache) 决定动画开始前如何获取初始值。

## 适配器模式
IThemeValueConverter 将原始值 (Color) 适配到平台类型 (Brush)。

## 单例模式
ThemeManager 是管理全局主题状态的静态单例。
