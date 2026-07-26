# Quick Start

## Responsibility

Write Quick Start guides for each functional module, showing the simplest, most declarative usage.

## Writing Principles

### Find the Simplest Entry Point

For each module, discover the simplest declarative usage by following this strict priority hierarchy:

> **Priority 1 — Demo/Example projects**
> Search the module's `Examples/` or `samples/` directory, **read all source files in full** for real-world usage code. Demo projects show the intended API surface and the most idiomatic patterns. Extract the minimal setup and usage from these files. Do not begin writing after reading only a subset of files.
>
> **Priority 2 — Unit Tests**
> If no Demo exists for a module, **read all test files in full**, scanning its test project(s) for test methods that exercise the API. Extract parameter construction, method invocation, and assertion patterns.
>
> **Priority 3 (Fallback) — Source code interfaces**
> Only when both Demo and Tests are absent: read the public API signatures from source files and construct minimal usage examples. Mark these as *inferred*.

### Simplest vs Detailed Pattern

For each API, identify its simplest declarative usage. When multiple usage patterns exist (e.g. extension methods, fluent builders, attribute-based, and low-level interface derivation), the Quick Start **must prioritize the highest-level, most encapsulated API** — the one that requires the least boilerplate from the user. Extension methods, fluent APIs, and attribute-based patterns are preferred; raw interface derivation and manual implementation should be mentioned only briefly, with a link to the API deep dive for full details.

| Pattern | Simplest (Quick Start) | Detailed (API Deep Dive) |
|---|---|---|
| Configuration | `services.AddX(opts => opts.Key = val)` | Custom `IConfigureOptions<X>` |
| Middleware | `app.UseX()` extension method | Custom `IMiddleware` implementation |
| Routing | `[Route]` + `[HttpGet]` attributes | Custom `IControllerActivator` |
| Logging | `ILogger<T>` DI injection | Custom `ILoggerProvider` |
| **Command/Property** | `[VeloxCommand]` / `[VeloxProperty]` attributes | Implementing `IVeloxCommand` / `INotifyPropertyChanged` manually |

### Example

Suppose we need to document a .NET background service Quick Start:

```markdown
### Adding a Background Service

1. Use the extension method to register a background service (top-level API):
```csharp
builder.Services.AddHostedService<DataSyncService>();
```

2. Create a class that inherits `BackgroundService`:
```csharp
public class DataSyncService : BackgroundService
{
	private readonly ILogger<DataSyncService> _logger;

	public DataSyncService(ILogger<DataSyncService> logger)
	{
		_logger = logger;
	}

	protected override async Task ExecuteAsync(CancellationToken stoppingToken)
	{
		while (!stoppingToken.IsCancellationRequested)
		{
			_logger.LogInformation("Syncing data...");
			await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
		}
	}
}
```
```

**Anti-pattern — wrong for Quick Start:** Showing `IHostedService` interface derivation and manual `Task` management first. The registration extension method and `BackgroundService` base class are the highest-level API and belong in Quick Start. Implementing `IHostedService` directly belongs in the API deep dive.

**Key principle for Quick Start:** If an attribute exists, use it. If a fluent API exists, use it. If a base class exists, inherit it. Save manual `interface` implementation for the API chapter.

### Formatting Requirements

- Each step uses a code block showing complete, runnable code
- Brief explanation before code (1-3 sentences)
- **Prioritize highest-level API** — attributes over interfaces, fluent over manual, extension methods over derivation
- Low-level or manual implementation patterns (e.g. directly implementing an interface) should be **briefly noted with "see API deep dive"**, not elaborated in Quick Start
- Advanced patterns marked as "see API deep dive"
- Output location: `content/{lang}/{category}/0_quickstart/` — create per-feature sub-pages under this outer directory

```
# Example: 1_Core with Workflow, MVVM, Transitions features
content/en/1_Core/0_quickstart/
├── index.md                    ← Overview
├── 0_Workflow/                 ← Feature sub-page
│   └── index.md
├── 1_MVVM/
│   └── index.md
└── 2_Transitions/
    └── index.md
```

## Post-Write Action

After writing Quick Start content:

- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run `dotnet build` to verify the new content embeds correctly
