# API Reference

## Responsibility

Fully enumerate all **interfaces, types, and functions** for each feature module, providing a complete API catalog with signatures.

## Writing Principles

### Full Coverage

API Reference is not about depth or multiple styles — it's about **uncompromising completeness**:

- List all public types (classes, structs, interfaces, enums) in each module
- For each type, list all public members (methods, properties, events, fields)
- Include full signature, parameter descriptions, return value descriptions, and exception declarations

### API Source

Use the「Feature Inventory」produced by the 【Analysis Paradigm】 as the source of truth: for features with Demo / Test evidence, extract the API surface from those Demos/tests; for features marked *inferred*, compile signatures from source and mark them accordingly.

### Entry Template

Record each public member using the following structure:

```markdown
### {TypeName}.{MemberName}

**Signature:**
`{ReturnType} {MemberName}({ParameterList})`

| Parameter | Type | Description |
|---|---|---|
| `{param}` | `{Type}` | {description} |

**Returns:** `{Type}` — {description}

**Exceptions:**
| Exception | Condition |
|---|---|
| `{ExceptionType}` | {condition} |

**Example:**
```text
// Source: [Demo/Test/Inferred]
result = instance.method(value);
```

**Notes:**
- {additional notes}
```

### Organization

Group by type, and within each type sort by member kind (properties first, then methods):

```markdown
## {Namespace/Package}

### Class: {ClassName}

#### Properties

| Name | Type | Description |
|---|---|---|
| `{Name}` | `{Type}` | {description} |

#### Methods

(Expand each using the entry template)

### Interface: {InterfaceName}

...
```

### Output Location

```
content/{lang}/{category}/1_API_Reference/{Feature}/
├── index.md                    ← Overview
├── 0_{Namespace/Package A}/
│   └── index.md
├── 1_{Namespace/Package B}/
│   └── index.md
└── ...
```

## Post-Write Action

After writing API documentation:

- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run the project's build command to verify the new content embeds correctly
