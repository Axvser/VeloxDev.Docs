# 过渡动画 — 前置条件

## 1. 支持的目标

**引擎内核**（来自 `VeloxDev.Core.csproj` 的 `<TargetFrameworks>`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`。引擎内核 —— 包括 `VeloxDev.Timing`、`VeloxDev.Threading` 与 `VeloxDev.Lifetime` —— 可由 .NET Framework 4.6.1+、.NET Core 3.0+ 与 .NET 5+ 消费。

**各框架适配器的目标**（来自各适配器 csproj）—— 动画化 UI 绑定属性时，添加与你 GUI 框架匹配的适配器：

| 适配器 | `<TargetFrameworks>` |
|---|---|
| `VeloxDev.WPF` / `VeloxDev.WinForms` | `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0` |
| `VeloxDev.Avalonia` | `netstandard2.0` / `net6.0` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0` |
| `VeloxDev.MAUI` | `net10.0` 加上 MAUI 工作负载提供的平台 TFM（Windows 上为 `net10.0-windows10.0.19041.0`） |
| `VeloxDev.Razor` | `net6.0` |
| `VeloxDev.Jalium` | `net10.0` |

**SDK / 运行时：** 一个能构建你所选目标的 .NET SDK。引擎内核不需要任何特殊工作负载；WPF / WinForms / WinUI / MAUI / Razor 目标需要相应 GUI 工作负载（`<UseWPF>true</UseWPF>`、Windows App SDK、MAUI 工作负载、Razor SDK）。仓库内演示构建在 `net9.0` / `net10.0` 上 —— 那是*已测*配置，不是最低要求。

**包管理器：** 经 `dotnet` CLI 或 Visual Studio 使用 NuGet（`dotnet add package ...`）。

**必需服务：** 无 —— 没有数据库、密钥或外部服务。要*看见* UI 动画需要一个运行中的应用宿主（WPF/Avalonia/WinUI/WinForms 窗口、MAUI 应用或 Blazor 回路）；纯值插值与整个 `VeloxDev.Timing` 层都可无头运行。

## 2. 示例的证据来源

本快速开始对照的演示位于 `Examples/Transition/`：

| 演示 | 目标框架 | 动画什么 |
|---|---|---|
| `WPF/Demo` | `net9.0-windows` | 五个 `Rectangle` —— 嵌套 `TranslateTransform.X`、一个 `TransformGroup`、`Fill`，以及五个过冲目标 |
| `Avalonia/Demo` | `net9.0` | 与 WPF 相同的场景集 |
| `WinUI/Demo` | `net8.0-windows10.0.19041.0` | `Rectangle` —— `RenderTransform`、`Projection`、渐变 `Fill` |
| `WinForms/Demo` | `net9.0-windows` | `Panel`/`Control` —— `Location`、`Size`、`BackColor` |
| `MAUI/Demo` | Windows 上 `net10.0-windows10.0.19041.0`（另有 `net10.0-android` / `-ios` / `-maccatalyst`） | MAUI `Rectangle` —— `TranslationX/Y`、`RotationX/Y`、`Scale`、`Fill` |
| `Blazor/Demo` | `net10.0`（服务端 + WASM 客户端） | 一个普通 `BoxModel` 视图模型，经 `INotifyPropertyChanged` 重渲染 |
| `Jalium/Demo` | `net10.0-windows` | Jalium 桌面 `Rectangle` |

引擎级契约另由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*`（26 个文件）与 `Src/Core/VeloxDev.Core.Test/Timing/*`（6 个文件）钉死。

## 3. `AUTO TEST` 一致性验收套件

`Examples/Transition/AUTO TEST/` 是本特性可获得的最强证据：一个一致性套件，它启动各演示的**可执行文件**，通过 UI Automation（Blazor 则通过 Playwright 驱动已安装的 Edge）驱动它们，并检查屏幕上实际发生了什么。它刻意**不**在 `VeloxDev.slnx` 中，因此仓库根目录的 `dotnet test` 保持纯后端 —— 请**按路径**运行它。

```bash
# 1. 先构建演示，且必须用这个形式（不要额外加 -p:Platform）
for p in WPF WinForms Avalonia MAUI WinUI Jalium; do dotnet build "Examples/Transition/$p/Demo/Demo.csproj" -c Debug; done
dotnet build "Examples/Transition/Blazor/Demo/Demo/Demo.csproj" -c Debug

# 2. 跑验收套件（陈旧的演示二进制看起来和代码 bug 一模一样）
cd "Examples/Transition/AUTO TEST"
VELOXDEV_AT=1 VELOXDEV_AT_PACE=0 VELOXDEV_AT_OBSERVE=0 VELOXDEV_BENCH_MS=200 dotnet test VeloxDev.AT.csproj --nologo
```

四个环境变量很重要：

| 变量 | 作用 |
|---|---|
| `VELOXDEV_AT=1` | **必需。** 没有它，每个 UI 测试都报为*跳过*且退出码 0 —— 这是从本项目得到「自信的错答案」最常见的方式。 |
| `VELOXDEV_AT_PLATFORMS` | 逗号分隔的子集，如 `WPF,Avalonia`。不设表示全部七个。 |
| `VELOXDEV_AT_PACE` / `VELOXDEV_AT_OBSERVE` | 每次点击后 / 每条用例前的暂停毫秒数。`0` = 只要结论；默认值（800 / 1200）= 人能看的一场运行。 |
| `VELOXDEV_BENCH_MS` | 每个演示用一条真实过渡把某个采样器跑多久。 |

每个平台跑四条用例，各钉住契约的一半：`ObservationSurface_IsReachableAndTicking`（启动路径、自动化树、自走的读数）、`LoadModes_MatchTheLibrarySemantics`（互斥与并发、UI 线程与后台 —— 以 `nomutual=` 观测）、`EverySamplerMatchesItsClosedForm`（采样器算术对照一份独立写就的闭式解，外加一条真实过渡运行）、`TimelineControl_SteersTheRunningAnimation`（对活着的动画做暂停 / 恢复 / 变速 / 定位）。Blazor 另加一条读浏览器自身计算样式的检查。

**本机已于 2026-10-01 核验：** 七个演示全部构建 0 错误；完整套件跑出 `测试运行成功。测试总数: 33 / 通过数: 32 / 跳过数: 1 / 总时间: 1.9579 分钟` —— 通过 32、失败 0、跳过 1（被 `[Ignore]` 的可达性压力测试）。原始输出见[验证与完整代码](../08_验证与完整代码/index.md)。
