# API Reference

## Responsibility

Fully enumerate all **interfaces, types, and functions** for each feature module, providing a complete API catalog with signatures.

## Writing Principles

### Full Coverage

API Reference is not about depth or multiple styles — it's about **uncompromising completeness**:

- List all public types (classes, structs, interfaces, enums) in each module
- For each type, list all public members (methods, properties, events, fields)
- Include full signature, parameter descriptions, return value descriptions, and exception declarations

**Coverage is a hard gate.** Every feature in the Feature Inventory must have an API page. For features with Demo/Test evidence, the public surface must be **fully enumerated** — every public type and member, no truncation. For *inferred* features, mark the page as such; partial coverage is allowed only there. After finishing, re-scan the module's public surface and diff it against what is documented; any missed API becomes an explicit residual.

### API Source

Use the「Feature Inventory」produced by the 【Analysis Paradigm】 as the source of truth: for features with Demo / Test evidence, extract the API surface from those Demos/tests; for features marked *inferred*, compile signatures from source and mark them accordingly.

**Update the inventory** — after finishing a feature, set its Coverage Status to `API ✓`.

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

Prefer a concrete call with **real input values and the resulting output**. If the sample needs environment setup (dependencies, service registration), reference the feature's Quick Start page instead of duplicating it.

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
Wiki_Root/2_API/00_{feature}/
├── index.md                    ← Overview
├── 00_{namespace-package-a}/
│   └── index.md
├── 01_{namespace-package-b}/
│   └── index.md
└── ...
```

> Feature directory names must match the Feature Inventory and be identical across the `1_QuickStart`, `2_API`, and `3_SE_Analysis` trees.

> When a namespace or feature API page would exceed ~300 lines, split further by type: `2_API/00_{feature}/00_{namespace}/00_{Type}/index.md` (or directly `2_API/00_{feature}/00_{Type}/index.md` when the feature has few namespaces).

## Post-Write Action

After writing API documentation:

- [ ] **Update the Feature Inventory** — set each documented feature's Coverage Status to `API ✓` (see module-discovery)
- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run the project's build command to verify the new content embeds correctly
