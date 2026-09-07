# Welcome Page

## Responsibility

Create a welcome page from a template that fits the current project

## Constraints

❌ Do not modify the established layout, e.g. changing the page size or wrapping in a ScrollViewer

✔ As a rule, do not change colors or animations unless the user explicitly asks

✔ Text content may be modified

✔ Feature entries may be removed

✔ Feature cards may be made **clickable** so they navigate to the page they describe: wrap a card's inner content in an `<a>` whose `href` follows the same-language cross-page link syntax in 【Links & Navigation】. From `0_Welcome/index.md`, sibling top-level sections live one level up — e.g. `<a href="../2_API/index.md">…</a>`; adapt the folder name (numeric prefix included) to this wiki's real tree. Do not alter layout, colors, or animations.

## Output Location

Wiki_Root/0_Welcome/index.md

## Template Selection

Choose a template from the 【Template Index】 table by matching the When column; use the one for “When creating the Wiki welcome page” by default.

The template is available in TWO forms — prefer the first:

- **Raw file (preferred)** — when a `Templates/welcome-default.md` file sits next to this SKILL (the installer ships module templates alongside SKILL.md), read the template body from that file directly. No decoding needed.
- **Escaped table cell (fallback)** — otherwise restore the cell from the 【Template Index】 row. The cell is a JSON string literal whose `|` characters are escaped as `\|` so the markdown table stays valid. Restore exactly in three steps: ① take the raw cell text; ② replace every `\|` with `|` (skip if the cell has none); ③ parse the result as a JSON string (`json.loads` / `JSON.parse`) to obtain the template body with real newlines.

Steps:

1. Obtain the template body — from the raw `Templates/welcome-default.md` file if present, otherwise decode the table cell per the fallback above
2. Adjust the text content and feature entries for the current project, then write to 【Output Location】
3. Follow 【Constraints】 throughout: do not modify the established layout; as a rule, do not change colors or animations
