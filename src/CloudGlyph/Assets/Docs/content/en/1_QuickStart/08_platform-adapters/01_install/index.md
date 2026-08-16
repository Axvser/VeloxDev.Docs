# Platform Adapters — Install / Add Dependency

Install the template package and add the adapter package:

```powershell
dotnet new install VeloxDev.WPF.Templates
dotnet add package VeloxDev.WPF
```

Pick the adapter package that matches your GUI framework. The `VeloxDev.WPF` package brings the workflow engine, the `VeloxDev.WorkflowSystem.AttachedBehaviors` namespace, and the WPF transition/theme wiring.

**Expected result:** the template package installs (`wpf-v-*` short names become available), and `VeloxDev.WPF` appears in the `.csproj` after `dotnet add package`.
