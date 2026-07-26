# .NET Documentation Conventions (C# / VB / F#)

## Applicable Scenario

Load this constraint when `.slnx` / `.sln` / `.csproj` / `.vbproj` / `.fsproj` is detected.

## Constraint Rules

### API Documentation Style

Use XML doc comments:

```xml
/// <summary>
/// Calculates the sum of two numbers.
/// </summary>
/// <param name="a">First addend</param>
/// <param name="b">Second addend</param>
/// <returns>The sum of a and b</returns>
/// <exception cref="ArgumentOutOfRangeException">Thrown when parameters are out of valid range</exception>
public int Add(int a, int b) => a + b;
```

### Visibility Recognition

- `public` = Public API, must be documented
- `internal` = Non-public, only document if `InternalsVisibleTo` is present
- `private protected` = Implementation detail, do not document
- Note `[EditorBrowsable(EditorBrowsableState.Never)]` and `[Obsolete]` attributes

### Async Patterns

```csharp
/// <summary>
/// Asynchronously gets user information
/// </summary>
/// <param name="userId">User identifier</param>
/// <param name="cancellationToken">Cancellation token</param>
public Task<User> GetUserAsync(int userId, CancellationToken cancellationToken = default)
```

### Dependency Injection

Document service DI lifetimes:

```csharp
// Singleton: One instance shared across the entire application
builder.Services.AddSingleton<IUserStore, InMemoryUserStore>();
// Scoped: One instance per request scope
builder.Services.AddScoped<IUserService, UserService>();
// Transient: A new instance on every injection
builder.Services.AddTransient<IEmailSender, EmailSender>();
```

### Nullability

Respect nullable reference types:

```csharp
// string? means it may be null
public string? GetOptionalValue(string key) { ... }
// string means it is not null
public string GetRequiredValue(string key) { ... }
```

### Naming Conventions

| Scope | Convention |
|---|---|
| Public members | `PascalCase` |
| Parameters | `camelCase` |
| Private fields | `_camelCase` |
| Interfaces | `I` + `PascalCase` |
