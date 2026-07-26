# Copyright

## Responsibility

Scan all common copyright/license files in the project root directory, organize the extracted information into a Wiki copyright page by category, **without omitting any found information**.

## Discovery Rules

Scan all of the following files and categorize the extracted information:

### Category List

| Category | Files to Scan | Content to Extract |
|---|---|---|
| **License Information** | `LICENSE` / `LICENSE.md` / `LICENSE.txt` | License type (MIT / Apache-2.0 / GPL-3.0 / BSD etc.), copyright holder, year |
| **Copyright Notice** | `COPYRIGHT` / `COPYRIGHT.md` | Full copyright notice text |
| **Contributors** | `AUTHORS` / `AUTHORS.md` / `CONTRIBUTORS` / `CONTRIBUTORS.md` | List of contributors |
| **Patent Grant** | `PATENTS` / `PATENTS.md` | Patent grant terms |
| **Third-party Notices** | `NOTICE` / `NOTICE.md` / `NOTICE.txt` | Third-party component copyright notices, preserving all attributions by section |

> Each category is scanned independently. If a category has no corresponding file, skip it without affecting other categories. If no files exist at all, skip this step entirely (no copyright page generated in the Wiki).

## Page Structure

The copyright page organizes categories in the following order:

```markdown
---
**License Information**

{Content extracted from LICENSE}

---

**Copyright Notice**

{Content extracted from COPYRIGHT}

---

**Contributors**

{List from AUTHORS / CONTRIBUTORS}

---

**Patent Grant**

{Content extracted from PATENTS}

---

**Third-party Component Notices**

{Third-party copyright notices from NOTICE}
```

> Categories without corresponding files are removed from the page entirely (no empty headings left).

## Examples

### Scenario: Project has LICENSE (MIT), AUTHORS.md, NOTICE.md

```markdown
---
**License Information**

Copyright (c) 2024 MyApp Contributors

This project is licensed under the [MIT License](LICENSE).

---

**Contributors**

- Alice
- Bob
- Carol

---

**Third-party Component Notices**

This project uses the following open-source components:

### Serilog
Copyright © 2013-2024 Serilog Contributors
MIT License

### Newtonsoft.Json
Copyright © James Newton-King 2008
MIT License
```

### Scenario: Project only has COPYRIGHT and PATENTS

```markdown
---
**Copyright Notice**

Copyright (c) 2024 MyApp Inc.
All rights reserved.

---

**Patent Grant**

Use of this software is subject to the patent grant terms (see PATENTS file):
...
```

## Output Location

`content/{lang}/{Project}/copyright/index.md`

One copy per language directory, content is the same.

## Post-Write Action

After writing Copyright content:

- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run `dotnet build` to verify the new content embeds correctly
