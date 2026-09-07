# Workflow System — Prerequisites

- **Supported targets** (from `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`):
    `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` — the library itself is usable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **SDK / runtime:** a modern .NET SDK. The component declarations on the next pages use **partial properties** (`[VeloxProperty] public partial QuickSlot InputSlot { get; set; }`), a C# 13 feature the generator consumes, so the SDK must ship Roslyn 4.12+ (**.NET SDK 9.0+**; this guide's sample targets `net10.0`, matching the repository's Trimmed demo generation).
- **Package manager:** NuGet / `dotnet` CLI (`dotnet new`, `dotnet add reference`, `dotnet restore`).
- **Required services:** none — the core engine is self-contained and runs headless. Python is needed only to run the *demo's* Python worker nodes (see [Verify & complete code](../07_complete-code/index.md)), not for this Quick Start.
- **Repository layout (ground truth for the walkthrough):**
    - Shared demo components & session builder: `Examples/Workflow/Common/Lib/ViewModels/Workflow/` (`ControllerViewModel.cs`, `TimerNodeViewModel.cs`, `EnumSelectorNodeViewModel.cs`, `WorkflowDemoSession.cs`, `Helper/*`).
    - Compiler / runtime-engine source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/` (`Compile/`, `Runtime/`).
    - Compiler contract tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`.

**Expected result:** you can run `dotnet --version` and get 9.0.x or newer, and you can open the repository's `VeloxDev.sln`.
