# Repo Reading — External Repository Reading Strategy & Understanding

> **Sub-skill.** Load only when the user asks to analyze an external repository (not Cloud Glyph itself).
> **Default path phase: Phase 1 (read-only, no Wiki output)**

External repo reading strategy: identify tech stack, entry points, dependency chain, and test structure to produce structured notes for downstream phases.

## When to Load

- "Analyze this repo"
- "Understand the project structure"
- "Where is the entry point"
- "What does this project do"
- "How is this project organized"

## Reading Strategy

1. **Identify project type** — Check `.sln`/`.csproj`/`package.json`/`package-lock.json`/`Cargo.toml`/`go.mod`/`pyproject.toml` to identify language and framework
2. **Start from the entry point** — `Program.cs`/`main.rs`/`index.ts`/`main.py`/`cmd/` etc.
3. **Follow the dependency chain** — From core model → service layer → API/Controller layer → UI layer
4. **Look at tests** — `*Test*/`/`*Spec*`/`tests/` directories reveal expected behavior and API usage

## Key Deliverables (Structured Notes)

| Item | Description | Downstream Consumer |
|---|---|---|
| Project type & tech stack | Language, framework, build tools | api-docs, se-analysis |
| Directory structure & module responsibilities | What each directory/project does | se-analysis |
| Entry points & core flow | How the app starts and requests flow | se-analysis |
| Public API list | Key exposed interfaces and classes | api-docs |
| Test directories & patterns | Test organization and assertion style | api-docs, se-analysis |
| Third-party dependencies | Key external dependencies and their purpose | All analysis phases |

## Role in the Default Path

- The output of this phase is **structured notes**, not written directly to the Wiki
- Notes are consumed as input by Phase 2 (API Docs) and Phase 3 (SE Analysis)
- Upon completion, auto-advance to Phase 2: `api-docs/SKILL.md`
