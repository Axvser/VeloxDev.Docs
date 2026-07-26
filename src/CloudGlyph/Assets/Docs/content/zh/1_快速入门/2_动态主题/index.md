# 动态主题 — 快速入门

VeloxDev 动态主题系统提供运行时主题切换，支持明暗主题间的平滑动画过渡。

## 设置

```csharp
using VeloxDev.DynamicTheme;

// 注册平台插值器（启动时调用一次）
ThemeManager.SetPlatformInterpolator(new VeloxDev.Avalonia.Interpolator());
```

## 定义主题

```csharp
public class MyDarkTheme : ITheme
{
	public Color Background => Color.FromRgb(30, 30, 30);
	public Color Foreground => Colors.White;
}

public class MyLightTheme : ITheme
{
	public Color Background => Colors.White;
	public Color Foreground => Colors.Black;
}
```

## 注册元素

```csharp
public class MyControl : IThemeObject
{
	public Color Background { get; set; }
}

ThemeManager.Register(myControl);
```

## 切换主题

```csharp
// 切换到暗色主题（带动画）
ThemeManager.Set<MyDarkTheme>();

// 无动画切换
ThemeManager.SetCurrent<MyDarkTheme>();
```

## 平台特定的主题值

每个平台适配器提供值转换器（如 Brush、Thickness），将原始主题值转换为 UI 特定类型。
