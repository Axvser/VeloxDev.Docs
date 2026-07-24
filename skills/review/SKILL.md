# Review — Wiki Content Review & Quality Checks

> **Sub-skill.** Load only when the user asks to review Wiki documentation quality.
> **Default path phase: Phase 5 (final quality gate)**

Audits Wiki content for broken links, structural consistency, rendering compatibility, multi-language parity, and **API existence verification** — every API reference in the written docs must be confirmed to exist in the target repository's source code.

## When to Load

- "Review documentation quality"
- "Check for broken links"
- "Audit Wiki content"
- "Validate documentation structure"
- "Ensure rendering compatibility"

## Checklist

- [ ] **Broken link detection** — All `[text](path)` references resolve correctly
- [ ] **Structural consistency** — Numeric prefixes follow conventions, all required `index.md` files exist
- [ ] **Rendering compatibility** — Mermaid/KaTeX/PlantUML syntax is correct and will render in AvalonMarkdown
      - [ ] Mermaid: direction/type valid, arrows correct, participants declared, brackets balanced
      - [ ] PlantUML: `@startuml`/`@enduml` balanced, participants declared, arrow directions explicit
      - [ ] KaTeX: all `$...$` and `$$...$$` inline/block pairs are balanced, no mismatched delimiters
- [ ] **Multi-language parity** — No missing or outdated pages across language versions
- [ ] **Discoverability** — Page titles and hierarchy are clear and navigable

### API Existence Verification (CRITICAL)

Every API reference appearing in the written documentation must be verified against the **actual source code** of the target repository. This includes:

- [ ] **Class/method names** in ` ``` ... ``` ` code examples — search the codebase to confirm each type and member exists with the documented signature
- [ ] **Namespace/module paths** in documentation — verify they match the actual project structure
- [ ] **Method parameters and return types** — cross-check against the source declaration; document must match reality
- [ ] **Exception declarations** — if the doc lists thrown exceptions, confirm they exist in the method signature or are documented in XML comments
- [ ] **Property/field names** — every property or field referenced in the doc must be present on the declared type
- [ ] **Removed/deprecated APIs** — if the target repo has `[Obsolete]` attributes or removed members, flag any doc references to them

### Pre-Commit Verification Flow

1. For every page in the Wiki, extract all code blocks containing API references
2. For each reference, use the repo-reading notes from Phase 1 or perform targeted symbol searches to confirm existence
3. If an API reference cannot be verified, **flag it for correction** — either fix the doc to match reality or remove the reference
4. Re-check diagram syntax (Mermaid/PlantUML) after any content corrections
5. Only after all items are ✅, mark the quality gate as passed
