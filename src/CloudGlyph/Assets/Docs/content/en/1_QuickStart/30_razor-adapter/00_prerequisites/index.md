# Prerequisites and install

## Supported targets

The adapter declares `net6.0;net8.0` and references the `Microsoft.AspNetCore.App` shared framework. Pick `net8.0` for a new project; the tested demo configuration is `net10.0`.

- .NET SDK 8.0 or later for `net8.0`. The ASP.NET Core shared framework ships with the SDK; there is no separate runtime install.
- A browser. The adapter's JS half runs client-side even when the component runs on the server.
- No database, service or API key.

## Packages

| Package | Version declared in this repository | Role |
| --- | --- | --- |
| `VeloxDev.Razor` | 12.3.0 | the components plus `wwwroot/veloxdev.workflow.js` and `.css` |
| `VeloxDev.Core` | 12.3.0 | model and canvas contracts, pulled transitively |
| `VeloxDev.Razor.Templates` | 12.0.0 | the seven `dotnet new` item templates |

## Project file

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="VeloxDev.Razor" Version="12.3.0" />
  </ItemGroup>
</Project>
```

The `Microsoft.NET.Sdk.Web` SDK brings the Blazor component model and static web assets.

## Register the render mode and the assets

`Program.cs` must add interactive server components and map the root component:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// .NET 8: static web assets come from UseStaticFiles.
// On .NET 9+ replace this with app.MapStaticAssets().
app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
```

`App` is the template's `Components/App.razor`. Two asset links belong in its `<head>` and `<body>`:

```html
<link rel="stylesheet" href="_content/VeloxDev.Razor/veloxdev.workflow.css" />
<!-- ... -->
<script src="_framework/blazor.web.js"></script>
```

The CSS is not optional: the surface's layout classes and the slot glyph sizing live there. The JS module is imported on demand by the components, so no extra script tag is needed.

## Install

```powershell
dotnet new blazor -n MyWorkflowApp
cd MyWorkflowApp
dotnet add package VeloxDev.Razor
dotnet new install VeloxDev.Razor.Templates
```

**Expected result:** the package restores, `Components/App.razor` loads the adapter stylesheet, and

```powershell
dotnet new list razor-v
```

lists `razor-v-tree`, `razor-v-node`, `razor-v-slot`, `razor-v-link`, `razor-v-selector`, `razor-v-decorator`, `razor-v-minimap`.

## Generate before the first build

The tree component references its siblings by bare type name through `@namespace` + `@using`. A partial suite does not compile. Generate all seven as shown in [Surface and host](../01_surface-and-host/index.md); the pack map is in [Workflow item templates](../../32_workflow-item-templates/index.md).

If a duplicate registration makes `dotnet new install` exit non-zero, run `dotnet new uninstall VeloxDev.Razor.Templates` first.
