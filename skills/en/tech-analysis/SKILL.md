# Tech Stack Analysis

## Responsibility

Deeply analyze the target codebase to identify the tech stack, entry points, module structure, and dependency chain. This skill provides foundational knowledge for all subsequent documentation writing.

## Analysis Steps

### 1. Identify Project Type

Check characteristic files in the root directory to determine the tech stack:

| Characteristic File | Tech Stack |
|---|---|
| `.slnx` / `.csproj` | .NET |
| `Cargo.toml` | Rust |
| `package.json` + `tsconfig.json` | TypeScript |
| `package.json` (no tsconfig) | JavaScript |
| `pyproject.toml` / `setup.py` | Python |
| `go.mod` | Go |
| `CMakeLists.txt` | C/C++ |
| `pom.xml` / `build.gradle` | Java |

### 2. Read Entry Files

Find and read the application's startup files (e.g. `Program.cs`, `main.rs`, `index.ts`, `main.py`) to understand the bootstrap flow.

### 3. Map Module Structure

Analyze directories layer by layer. Do not guess based on directory names; instead read representative files in each directory to confirm its purpose.

### 4. Build Dependency Graph

Read project/package definition files and record external dependencies and their purposes.

## Example

```
Project: MyApp (C# .NET 8)
├── src/
│   ├── MyApp.Core/       ← Entities, Domain Services
│   │   ├── Models/       ← Data models
│   │   └── Services/     ← Business logic
│   └── MyApp.Web/        ← ASP.NET Core Web API
│       ├── Controllers/  ← API endpoints
│       └── Middleware/   ← Pipeline middleware
├── tests/
│   └── MyApp.Tests/      ← xUnit tests
└── docs/                 ← Documentation directory

Dependencies: ASP.NET Core 8.0, Entity Framework Core, Serilog
```

## Output

- Tech stack inventory (language, framework, runtime)
- Module responsibility table (confirmed purpose of each directory)
- Dependency graph

## Reading Strategy

1. **Identify project type** — Check `.sln`/`.csproj`/`package.json`/`package-lock.json`/`Cargo.toml`/`go.mod`/`pyproject.toml` to identify language and framework
2. **Start from the entry point** — `Program.cs`/`main.rs`/`index.ts`/`main.py`/`cmd/` etc.
3. **Follow the dependency chain** — From core model → service layer → API/Controller layer → UI layer
4. **Look at tests** — `*Test*/`/`*Spec*`/`tests/` directories reveal expected behavior and API usage

## Key Deliverables (Structured Notes)

| Item | Description | Downstream Consumer |
|---|---|---|
| Project type & tech stack | Language, framework, build tools | api-docs, se-analysis |
| Directory structure & module responsibilities | What each directory/project does | se-analysis |
| Entry points & core flow | How the app starts and requests flow | se-analysis |
| Public API list | Key exposed interfaces and classes | api-docs |
| Test directories & patterns | Test organization and assertion style | api-docs, se-analysis |
| Third-party dependencies | Key external dependencies and their purpose | All analysis phases |

## Role in the Default Path

- The output of this phase is **structured notes**, not written directly to the Wiki
- Notes are consumed as input by Phase 6 (API Docs) and Phase 7 (SE Analysis)
- Upon completion, auto-advance
