# Context Setup

## Responsibility

Confirm all necessary context

## Flow

1. Derive CloudGlyph_Child_Git from MainSKILL_Path

2. Project_Root must be provided by the user

3. LanguageTargets_List must be provided by the user, and must be a subset of LanguageMap_List; if not, inform the user that LanguageMap_List needs to be edited to support the specified languages

4. Identify the project's tech stack (programming languages, frameworks, build tools, package managers, etc.) without presuming any specific technology

5. Optionally accept a SKILL path from the user; if provided, load the corresponding SKILL

6. **Scan existing Wiki_Root content** — Examine the current file structure under Wiki_Root for each target language, record the existing page tree, identify which dimensions already have content and which are empty, and pass this information to the writing phases. Treat any page already present as a **prior valid output**: record it in the working state (path + the dimension it serves) so later phases update it in place and so the Review phase's cleanup can tell prior-run pages from stray ones. This step never deletes anything — deletion decisions live only in the Review phase and target only pages that are neither on this run's output list nor a prior page the Feature Inventory still covers.

7. Present a summary table to the user; proceed with the workflow after user confirmation
