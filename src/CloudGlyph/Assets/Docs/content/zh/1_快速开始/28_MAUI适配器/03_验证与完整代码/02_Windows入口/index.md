# Windows 入口

MAUI 单工程应用需要 `Platforms/Windows/` 下的 Windows 入口。下面三个文件是表面本身不提供的；MAUI 工程模板还会生成 `Package.appxmanifest`，保留即可。

## Platforms/Windows/App.xaml

```xml
<maui:MauiWinUIApplication
    x:Class="MyApp.WinUI.App"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:maui="using:Microsoft.Maui"
    xmlns:local="using:MyApp.WinUI">
</maui:MauiWinUIApplication>
```

## Platforms/Windows/App.xaml.cs

```csharp
using Microsoft.Maui;
using MyApp;

namespace MyApp.WinUI;

public partial class App : MauiWinUIApplication
{
    public App() => InitializeComponent();

    protected override MauiApp CreateMauiApp() => MauiProgram.CreateMauiApp();
}
```

## Platforms/Windows/app.manifest

```xml
<?xml version="1.0" encoding="utf-8"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <assemblyIdentity version="1.0.0.0" name="MyApp.WinUI.app" />
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/PM</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2, PerMonitor</dpiAwareness>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </windowsSettings>
  </application>
</assembly>
```

**预期结果：** `dotnet build -t:Run -f net10.0-windows10.0.19041.0` 启动应用，`MainPage` 成为窗口内容。

## 运行声明

- ⚠️ 未实际运行 —— 仅做了静态核对。`MauiWinUIApplication` 入口、`MauiProgram.CreateMauiApp` 钩子、附着属性命名空间、`WorkflowLinkOverlay` 的 `WorkflowTree` / `InteractionSource` / 偏移属性与 ViewModel 特性均对照过 `Src/Adapters/VeloxDev.MAUI/`、`Src/Core/VeloxDev.Core/` 与 `Examples/Workflow/MAUI Trimmed/Demo/`。Windows 入口与共享文件在本次写作中未编译、未执行。
