# Migration — Migration Guides & Version Upgrade Documentation

> **Sub-skill.** Load only when the user asks to write a migration guide or upgrade documentation.

## When to Load

- "Migrate from .NET Framework to .NET 8"
- "Upgrade guide for the latest version"
- "Breaking changes documentation"
- "Migrate from library A to library B"

## Document Structure

| Section | Content |
|---|---|
| Overview | Why migrate, target version, benefits |
| Prerequisites | Environment requirements, dependency version check |
| Breaking Changes | Breaking changes listed by module with mitigation |
| Migration Steps | Phased migration workflow (prepare → migrate → verify → deploy) |
| API Mapping | Old API → New API comparison table |
| Rollback Plan | How to revert if something goes wrong |
| FAQ | Common pitfalls during migration |

## Output Requirements

- Use KaTeX formulas to display version compatibility matrices
- Use tables to contrast old vs new behavior
- Use code blocks to show "before vs after" comparisons
