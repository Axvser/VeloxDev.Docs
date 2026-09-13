# Welcome Page

## Responsibility

Create a welcome page from a template that fits the current project

## Constraints

❌ Do not modify the established layout, e.g. changing the page size or wrapping in a ScrollViewer

✔ As a rule, do not change colors or animations unless the user explicitly asks

✔ Text content may be modified

✔ Feature entries may be removed

⚙ **Feature cards ARE links — not an option.** Wrap each card's content in `<a class="feat-link" href="…">` so the card itself is clickable. The destination is the **QuickStart page of the feature the card names**; when a feature has no QuickStart page of its own, the QuickStart section overview is the correct destination. `href` follows the same-language cross-page link syntax in 【Links & Navigation】 — from `0_Welcome/index.md`, the other top-level dimensions live one level up, e.g. `../1_QuickStart/index.md` or `../1_QuickStart/00_user-registration/index.md`. Directory names carry their numeric prefix; adapt them to this wiki's real tree. The card text is the label — the link carries no additional visible text. Keep the `.feat-link` rule that makes the link invisible as a link.

⚙ **The page is the template body and nothing else.** The hero (title, subtitle, rule, workflow steps, feature cards) is the whole page. Do NOT append prose paragraphs, tables, feature inventories, "Explore the documentation" sections, repository links or any other block after the closing `</div>`. Everything that would go there belongs on a QuickStart, API or SE Analysis page.

⚙ **No tagline row of dot-separated claims.** Do not add a trailing line of the form `· No database · Open source · MIT` (the template's former `.glow-dot` row). Any such claim either belongs in a card or nowhere.

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
