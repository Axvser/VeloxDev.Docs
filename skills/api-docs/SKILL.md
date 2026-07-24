# API Docs — Test-Driven API Documentation

> **Sub-skill.** Load only when the user asks to write API documentation based on an external repository's test code.
> **Default path phase: Phase 2**
> **Prerequisite:** Phase 1 (repo-reading) complete — structured notes available

Discovers API best practices from test code (assertions, signatures, input/output patterns) and produces structured reference documentation.

## When to Load

- "Write API docs from tests"
- "Extract API documentation from test code"
- "Generate API reference from test cases"
- "Document public API based on tests"

## Method

1. **Locate test directories** — `*Test*/`/`*Spec*`/`*Tests*`/`*Integration*`/`tests/`
2. **Identify test patterns** — `Assert`/`Should`/`Expect`/`Verify`/`AssertThat` and similar assertion styles
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
