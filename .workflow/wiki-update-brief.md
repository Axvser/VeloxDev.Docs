# Wiki update brief — 2026-10-18

## Paths

- **Project root**: `E:\VisualStudio\Projects\VeloxDev`
- **Wiki child repo**: `E:\VisualStudio\Projects\VeloxDev\Docs\VeloxDev.Docs`
- **Wiki content root**: `<child>/src/CloudGlyph/Assets/Docs/content`
- **Skill**: `E:\VisualStudio\Projects\VeloxDev\.claude\skills\cloud-glyph-wiki-create\SKILL.md`
- **Reviewer**: `<child>/skills/wiki-reviewer.md`
- **Languages**: `en`, `zh`

## Scope (user-approved)

- **All 10 modules**.
- **en**: update QuickStart / API / SE Analysis — correctness against source, more concise, reproducible.
- **zh**: create the missing QuickStart and SE Analysis trees, mirroring the en tree shape (translated directory names); sync the existing zh API with the corrected en API.
- Cross-dimension names must stay consistent within each language.
- Do **not** rename existing feature directories. Do **not** edit another module, the shared parent indexes, or `0_Welcome` / `4_Copyright` (the coordinator handles those). Do **not** commit.

## Module map

| # | en dir | zh dir | Source roots |
|---|---|---|---|
| 00 | `workflow-system` | `工作流系统` | `Src/Core/VeloxDev.Core/WorkflowSystem`, `Interfaces/WorkflowSystem`, `Src/Adapters/*/Attached/Workflow`, `Examples/Workflow`, `Src/Core/VeloxDev.Core.Test/WorkflowSystem` |
| 01 | `workflow-agent` | `工作流代理` | `Src/Core/VeloxDev.Core.Extension/Agent`, `Examples/Workflow/Common/Lib`, `Src/Core/VeloxDev.Core.Extension.Test` |
| 02 | `mvvm` | `MVVM` | `Src/Core/VeloxDev.Core/MVVM`, `Interfaces/MVVM`, `Src/Generators/VeloxDev.Core.Generator`, `Examples/MVVM`, tests |
| 03 | `transition` | `过渡动画` | `Src/Core/VeloxDev.Core/TransitionSystem`, `Interfaces/TransitionSystem`, `Src/Adapters/*/PlatformAdapters`, `Examples/Transition` |
| 04 | `dynamic-theme` | `动态主题` | `Src/Core/VeloxDev.Core/DynamicTheme`, `Interfaces`, adapters, `Examples/Theme` |
| 05 | `aop` | `AOP` | `Src/Core/VeloxDev.Core/AspectOriented`, `Interfaces`, generator, `Examples/AOP` |
| 06 | `tickable` | `Tickable` | `Src/Core/VeloxDev.Core/TimeLine`, `Interfaces`, generator, `Examples/Tickable` |
| 07 | `weak-types` | `弱引用类型` | `Src/Core/VeloxDev.Core/WeakTypes`, `Interfaces`, tests |
| 08 | `platform-adapters` | `平台适配器` | `Src/Adapters`, `Src/Templates`, `Examples/Workflow`, `Examples/Transition` |
| 09 | `serialization` | `序列化` | `Src/Core/VeloxDev.Core/Serialization`, `Interfaces`, `Src/Generators`, `Src/Core/VeloxDev.Core.Extension` |

Existing zh API dirs are the authority for the Chinese module names. The zh QuickStart/SE Analysis must reuse them.

## Quality contract

1. **Correctness first** — every type, member, namespace, signature, exception, file path, and command must be checked against the source. The existing en pages are a draft, not ground truth. Never invent APIs.
2. **Concise** — remove duplicated prose, repeated tables, and step-by-step narration that adds no information. Keep the actionable path: prerequisites → install → setup → usage → verify. Split pages over ~300 lines or 3 distinct topics; the parent `index.md` becomes a short overview.
3. **Reproducible QuickStart** — prerequisites come from the project's declared TFMs/package minimums, not a demo's runtime. Every numbered step has an observable **Expected result**. Complete code has no `...`. The page ends with an honest **Run Declaration**: `✅` only with recorded output, otherwise `⚠️` static verification.
4. **Code authenticity** — every code block is traceable to a real file (cite path). Prefer demo/test snippets. Use real spaces, never tabs. Keep identifiers/code blocks identical in zh pages; translate prose only.
5. **Structure** — every directory has `index.md`; two-digit prefixes; cross-language tree shape parity; no new local links where the parent tree already navigates (existing links may stay).
6. **zh parity** — mirror the en page tree under `1_QuickStart/<zh module>` and `3_SE_Analysis/{02_设计模式,03_数据流,04_复杂度}/<zh module>`. Translate and condense; do not translate code identifiers. Keep the same sub-page numbering/names translated.
7. **Do not touch** — other modules, `1_QuickStart/index.md`, `2_API/index.md`, `3_SE_Analysis/index.md`, the five SE group `index.md` files, `0_Welcome`, `4_Copyright`. The coordinator owns them.
8. **Report** — list changed files per language/dimension, any residual gaps, and any source references you could not verify. Do not commit or run `git` write commands.

## Time budget

Prioritize in this order: (1) en correctness + concision, (2) zh QuickStart/API parity with correct identifiers, (3) zh SE Analysis translation. If a page cannot be fully verified, mark it `⚠️` rather than claiming `✅`.
