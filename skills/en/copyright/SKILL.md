# Copyright

## Responsibility

`Discover` copyright/license/attribution files or information under 【Project_Root】, `organize` into the Wiki

## Discovery

Scan the following files and categorize the extracted information

| Category | Files to Scan | Content to Extract |
|---|---|---|
| **License Information** | `LICENSE` / `LICENSE.md` / `LICENSE.txt` | License type (MIT / Apache-2.0 / GPL-3.0 / BSD etc.), copyright holder, year |
| **Copyright Notice** | `COPYRIGHT` / `COPYRIGHT.md` | Full copyright notice text |
| **Contributors** | `AUTHORS` / `AUTHORS.md` / `CONTRIBUTORS` / `CONTRIBUTORS.md` | List of contributors |
| **Patent Grant** | `PATENTS` / `PATENTS.md` | Patent grant terms |
| **Third-party Notices** | `NOTICE` / `NOTICE.md` / `NOTICE.txt` | Third-party copyright notices, preserve all attributions by section |

## Organization

Organize categories in the following order by {type}:

```markdown
---
**License Information**

{Content from LICENSE}

---

**Copyright Notice**

{Content from COPYRIGHT}

---

**Contributors**

{List from AUTHORS / CONTRIBUTORS}

---

**Patent Grant**

{Content from PATENTS}

---

**Third-party Notices**

{Content from NOTICE}
```

> If no files found for a category, do not create a sub-page for it

> Use copy/paste to obtain original text, avoid LLM hallucination

## Output Location

Wiki_Root/content/{language}/4_Copyright/{type}/index.md
