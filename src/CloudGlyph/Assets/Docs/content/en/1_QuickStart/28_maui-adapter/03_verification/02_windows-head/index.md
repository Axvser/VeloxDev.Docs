# Windows Head

A MAUI single-project app needs a Windows entry point under `Platforms/Windows/`. These are the three files the surface itself does not provide; the MAUI project template also emits `Package.appxmanifest`, which can stay in place.

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

**Expected result:** `dotnet build -t:Run -f net10.0-windows10.0.19041.0` starts the app and `MainPage` becomes the window content.

## Run Declaration

- ⚠️ Not actually run — statically verified only. The `MauiWinUIApplication` entry point, the `MauiProgram.CreateMauiApp` hook, the attached property namespace, the `WorkflowLinkOverlay` properties (`WorkflowTree`, `InteractionSource`, offsets) and the ViewModel attributes were checked against `Src/Adapters/VeloxDev.MAUI/`, `Src/Core/VeloxDev.Core/` and `Examples/Workflow/MAUI Trimmed/Demo/`. The Windows head and the shared files were not compiled or executed in the writing session.
