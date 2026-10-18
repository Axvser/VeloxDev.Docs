# 过渡动画 — 前置条件

## 1. 支持的目标框架

**引擎核心**（来自 `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj` 的 `<TargetFrameworks>`）：`netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` / `net8.0`。引擎核心 —— 包括 `VeloxDev.Timing`、`VeloxDev.Threading` 与 `VeloxDev.Lifetime` —— 可从 .NET Framework 4.6.1+、.NET Core 3.0+、.NET 5+ 与 .NET 8+ 使用。

动画 UI 绑定属性时，再按 GUI 框架加入对应适配器（目标框架取自各适配器 csproj）：

| 适配器 | `<TargetFrameworks>` |
|---|---|
| `VeloxDev.WPF` / `VeloxDev.WinForms` | `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0` / `net8.0-windows` |
| `VeloxDev.Avalonia` | `netstandard2.0` / `net6.0` / `net8.0` |
| `VeloxDev.WinUI` | `net8.0-windows10.0.19041.0` / `net10.0-windows10.0.19041.0` |
| `VeloxDev.MAUI` | `net10.0` / `net10.0-windows10.0.19041.0`（其它平台目标由 MAUI 工作负载提供） |
| `VeloxDev.Razor` | `net6.0` / `net8.0` |
| `VeloxDev.Jalium` | `net10.0` |

**预期结果：** 你能在所选适配器的 TFM 列表里找到自己的目标；本快速开始最后一页的 WPF 程序使用 `net9.0-windows`（仓库 demo 的*经过测试*配置，不是最低要求）。

## 2. SDK / 运行时

能构建所选目标的 .NET SDK：`net8.0` 目标需要 .NET 8 SDK 或更新，`net10.0` 目标需要 .NET 10 SDK。引擎核心不需要特殊工作负载；WPF / WinForms / WinUI / MAUI / Razor 目标需要相应 GUI 工作负载（`<UseWPF>true</UseWPF>`、Windows App SDK、MAUI 工作负载、Razor SDK）。仓库内 demo 以 `net9.0` / `net10.0` 构建 —— 那是*经过测试*的配置，不是要求。

**预期结果：** `dotnet --list-sdks` 列出你准备使用的 SDK；构建 `net8.0` 目标时其中包含 8.x 或更新版本，构建 `net10.0` 目标时包含 10.x。

## 3. 包管理器

NuGet，经 `dotnet` CLI 或 Visual Studio（`dotnet add package ...`）。

**预期结果：** `dotnet add package VeloxDev.Core` 能解析到包并写入 `.csproj`。

## 4. 必需服务

无 —— 不需要数据库、密钥或外部服务。要*看到* UI 动画，需要一个运行中的应用宿主（WPF/Avalonia/WinUI/WinForms 窗口、MAUI 应用或 Blazor 回路）；纯值插值与整个 `VeloxDev.Timing` 层都可以无界面运行。

**预期结果：** 一个空控制台项目就能完成缓动、采样器与时间层示例；只有 UI 动画需要一个图形宿主。

## 5. 示例与证据

本快速开始镜像的 demo 位于 `Examples/Transition/`：

| Demo | 目标框架 | 动画对象 |
|---|---|---|
| `WPF/Demo` | `net9.0-windows` | 五个 `Rectangle` —— 嵌套的 `TranslateTransform.X`、`TransformGroup`、`Fill`，以及五个过冲目标 |
| `Avalonia/Demo` | `net9.0` | 与 WPF 相同的场景集 |
| `WinUI/Demo` | `net8.0-windows10.0.19041.0` | `Rectangle` —— `RenderTransform`、`Projection`、渐变 `Fill` |
| `WinForms/Demo` | `net9.0-windows` | `Panel`/`Control` —— `Location`、`Size`、`BackColor` |
| `MAUI/Demo` | Windows 上 `net10.0-windows10.0.19041.0`（另有 `net10.0-android` / `-ios` / `-maccatalyst`） | MAUI `Rectangle` —— `TranslationX/Y`、`RotationX/Y`、`Scale`、`Fill` |
| `Blazor/Demo` | `net10.0`（server + WASM client） | 普通 `BoxModel` 视图模型，经 `INotifyPropertyChanged` 重渲染 |
| `Jalium/Demo` | `net10.0-windows` | Jalium 桌面 `Rectangle` |

引擎级契约另由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/*`（26 个文件）与 `Src/Core/VeloxDev.Core.Test/Timing/*`（6 个文件）钉住 —— 共 287 个 MSTest 用例。

**预期结果：** 你知道每个 demo 的目标框架，并能区分「demo 的测试配置」与「库支持的最低目标」。

## 6. `AUTO TEST` 一致性验收套件

`Examples/Transition/AUTO TEST/` 是本特性最强的证据：它启动每个 demo 的**可执行文件**，通过 UI Automation（Blazor 则通过 Playwright 驱动已安装的 Edge）操作界面并检查屏幕上实际发生了什么。它刻意**不在** `VeloxDev.slnx` 里，因此仓库根目录的 `dotnet test` 仍只跑后端 —— 请**按路径**运行它。

```bash
# 1. 先按这个形式构建 demo（不要额外加 -p:Platform）
for p in WPF WinForms Avalonia MAUI WinUI Jalium; do dotnet build "Examples/Transition/$p/Demo/Demo.csproj" -c Debug; done
dotnet build "Examples/Transition/Blazor/Demo/Demo/Demo.csproj" -c Debug

# 2. 运行验收套件（过期的 demo 二进制看起来和代码 bug 一模一样）
cd "Examples/Transition/AUTO TEST"
VELOXDEV_AT=1 VELOXDEV_AT_PACE=0 VELOXDEV_AT_OBSERVE=0 VELOXDEV_BENCH_MS=200 dotnet test VeloxDev.AT.csproj --nologo
```

四个环境变量：

| 变量 | 作用 |
|---|---|
| `VELOXDEV_AT=1` | **必需。** 没有它，所有 UI 测试都会报告为*跳过*并以 0 退出 —— 这是本项目最容易得到「自信的错误答案」的方式。 |
| `VELOXDEV_AT_PLATFORMS` | 逗号分隔的子集，例如 `WPF,Avalonia`。未设置表示全部七个。 |
| `VELOXDEV_AT_PACE` / `VELOXDEV_AT_OBSERVE` | 每次点击后 / 每个用例前的暂停毫秒数。`0` = 只取结论；默认值（800 / 1200）= 人眼可看的运行。 |
| `VELOXDEV_BENCH_MS` | 每个 demo 用真实过渡播放一个采样器的时间。 |

每个平台运行四个用例：`ObservationSurface_IsReachableAndTicking`（启动路径、自动化树、自滴答读数）、`LoadModes_MatchTheLibrarySemantics`（互斥与并发、UI 线程与后台线程）、`EverySamplerMatchesItsClosedForm`（用独立闭式解核对采样器算术并跑真实过渡）、`TimelineControl_SteersTheRunningAnimation`（对活动动画暂停 / 恢复 / 变速 / 定位）。Blazor 另有第五个用例，读取浏览器的 computed style。

**预期结果（记录，2026-10-01）：** 七个 demo 全部 0 错误构建；完整套件报告 `测试运行成功。测试总数: 33 / 通过数: 32 / 跳过数: 1 / 总时间: 1.9579 分钟` —— 32 通过、0 失败、1 跳过（被 `[Ignore]` 的可达性压力测试）。原始输出见[验证与完整代码](../08_验证与完整代码/index.md)。
