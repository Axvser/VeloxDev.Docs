# 平台适配器 — 安装 / 添加依赖

安装模板包并添加适配器包：

```powershell
dotnet new install VeloxDev.WPF.Templates
dotnet add package VeloxDev.WPF
```

选择与你 GUI 框架匹配的适配器包。`VeloxDev.WPF` 包会带来工作流引擎、`VeloxDev.WorkflowSystem.AttachedBehaviors` 命名空间以及 WPF 过渡/主题接线。

**预期结果：** 模板包装好（`wpf-v-*` 短名可用），执行 `dotnet add package` 后 `.csproj` 中出现 `VeloxDev.WPF`。
