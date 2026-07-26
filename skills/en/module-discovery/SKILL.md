# Module Discovery

## Responsibility

Analyze the solution structure to systematically discover all functional modules and their responsibility boundaries. This skill provides the module inventory for subsequent Quick Start, API documentation, and software engineering analysis.

## Workflow

### 1. Scan Project Structure

List all projects/directories under Solution_Root and read each project's definition file:

```
# .NET example
Solution: MyApp.slnx
├── src/MyApp.Core/          ← Class library
│   └── MyApp.Core.csproj
├── src/MyApp.Web/           ← Web application
│   └── MyApp.Web.csproj
└── tests/MyApp.Tests/       ← Test project
	└── MyApp.Tests.csproj
```

### 2. Identify Module Responsibilities

For each project, read its internal directory structure and representative files:

```
# Read MyApp.Web's Controllers/ directory
# Confirms this is an ASP.NET Core Web API module
# Purpose: Provides RESTful API endpoints
```

**Critical: Also check for Demo/Example and Test projects related to each module.** These reveal the actual API surface and idiomatic usage patterns:

```
# Examples/MyApp.Web/ contains a working REST API demo
# → Extract endpoint patterns, middleware setup, DI registration

# tests/MyApp.Web.Tests/ has controller tests
# → Extract request construction, status code assertions
```

### 3. Map Dependencies

Read ProjectReference and PackageReference from `.csproj` / equivalent files:

```xml
<ItemGroup>
  <ProjectReference Include="..\MyApp.Core\MyApp.Core.csproj" />
  <PackageReference Include="Serilog.AspNetCore" Version="8.0.0" />
</ItemGroup>
```

### 4. Generate Module Responsibility Table

| Module | Type | Responsibility | Dependencies |
|---|---|---|---|
| MyApp.Core | Class Library | Domain models, business logic | None |
| MyApp.Web | Web Application | REST API, middleware | MyApp.Core, Serilog |
| MyApp.Tests | Tests | Unit tests, integration tests | xUnit, MyApp.Core |

## Output

- Complete module list (name, path, type)
- Confirmed responsibility for each module (based on file content, not guesswork)
- Inter-project dependency graph
