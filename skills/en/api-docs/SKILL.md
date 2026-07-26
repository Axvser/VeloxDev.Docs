# APIs

## Responsibility

Write complete API reference documentation for each functional module. More in-depth than Quick Start, showing all usage patterns (declarative + imperative), including security coverage.

## Writing Requirements

### API Discovery Priority

When extracting API documentation, follow this strict priority hierarchy:

> **Priority 1 — Demo/Example projects**
> Scan `Examples/` directories for real-world usage of the API, **read all source files in full**. Demo projects reveal the intended public API surface and the most idiomatic invocation patterns.
>
> **Priority 2 — Unit Tests**
> **Read all test files in full**, extracting API signatures, typical input/output, and edge cases. Tests provide real parameter values, assertion expectations, and exception paths.
>
> **Priority 3 (Fallback) — Source code interfaces**
> Only when no Demo or Test exists: read the public API signatures directly from source files. These must be explicitly marked as *inferred*.

### Semantic Level

- What problem does this API solve? (high-level intent, not just the method name)
- When to use vs alternatives
- Preconditions and postconditions

### Full Code Level

```csharp
/// <summary>
/// Asynchronously gets user information
/// </summary>
/// <param name="userId">User unique identifier</param>
/// <param name="cancellationToken">Cancellation token</param>
/// <returns>User object, or null if not found</returns>
/// <exception cref="ArgumentException">Thrown when userId is invalid</exception>
/// <exception cref="HttpRequestException">Thrown on network error</exception>
public async Task<User?> GetUserAsync(
	int userId,
	CancellationToken cancellationToken = default)
```

### Exception Table

| Exception | Condition |
|---|---|
| `ArgumentException` | `userId <= 0` |
| `HttpRequestException` | Network request failed |
| `TimeoutException` | No response within 30 seconds |

### Multiple Usage Styles

Show both declarative and imperative usage:

```csharp
// Declarative (Quick Start style)
[HttpGet("users/{id}")]
public async Task<IActionResult> GetUser(int id)

// Imperative (full control)
var endpoint = app.MapGet("/users/{id}", async (int id) => { ... });
endpoint.WithName("GetUser");
endpoint.WithOpenApi();
```

### Security Coverage

- Authentication/authorization requirements
- Input validation logic
- Data sensitivity notes
- Security defaults

## Output Location

`content/{lang}/{category}/1_api/{Feature}/index.md`

Each feature module gets its own sub-directory:

```
# Example: 1_Core API reference
content/en/1_Core/1_api/
├── index.md                    ← Overview
├── 0_Workflow/                 ← Workflow API
│   └── index.md
├── 1_MVVM/                     ← MVVM API
│   └── index.md
├── 2_Transitions/              ← Transitions API
│   └── index.md
└── ...
```

3. **Extract API signatures** — Method name, parameter types, return type, exception declarations
4. **Record typical input/output** — Extract real invocation examples from test cases
5. **Capture edge cases** — `null`, empty collections, boundary values, error paths
6. **Generate documentation** — API signature → parameter table → return value → example code → notes/caveats

## Document Template

```markdown
## ClassName.MethodName

**Signature:** `ReturnType MethodName(ParamType1 param1, ParamType2 param2)`

| Parameter | Type | Description |
|---|---|---|
| `param1` | `ParamType1` | Description of param1 |
| `param2` | `ParamType2` | Description of param2 |

**Returns:** `ReturnType` — Description of return value

**Example:**

```csharp
// From test: TestClass.Should_X_When_Y
var result = instance.MethodName(value1, value2);
Assert.Equal(expected, result);
```

**Notes:**
- May throw YException when X occurs
- Null values cause Z behavior
```

## Post-Write Action

After writing API documentation:

- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run `dotnet build` to verify the new content embeds correctly
