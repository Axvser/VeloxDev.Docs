# VeloxDev — Feature Inventory

> Working artifact produced by the `cloud-glyph-wiki-create` skill (module-discovery step).
> The feature set is **FROZEN** after discovery. Steps 3–5 only mark the Coverage Status column;
> they never add, remove, or rename features.
> Regenerated each run — a future template sync removing it is expected.
>
> **Re-derived 2026-10-05** (discovery order: README → Examples → Tests → source). Supersedes the 2026-10-01 set.

## Feature Inventory

| # | Feature | Owning Project | Evidence | Coverage Status |
|---|---|---|---|---|
| 00 | workflow-system | `VeloxDev.Core` (`WorkflowSystem/`, `GUI/Events/Input/`) + `VeloxDev.Core.Extension` (`CompiledGraphEx`, `CheckpointEx` — the document wrappers only) | Demo (`Examples/Workflow/*`, 7 platforms + Trimmed) + Test (`VeloxDev.Core.Test/WorkflowSystem/` ≈35 files) | QS ✓ / API ✓ / SE ✓ |
| 01 | workflow-agent | `VeloxDev.Core.Extension` (`Agent/`) + `VeloxDev.Core` (`AI/`) | Demo (Agent pane in all 7 platform demos, via `Examples/Workflow/Common/Lib/.../AgentHelper.cs`) + Test (`VeloxDev.Core.Extension.Test/Agent/**` 25 files, `VeloxDev.Core.Test/AI/*` 7 files) | QS ✓ / API ✓ / SE ✓ |
| 02 | mvvm | `VeloxDev.Core` (`MVVM/`, `Interfaces/MVVM/`) | Demo (`Examples/MVVM/WPF`, `Examples/MVVM/Avalonia`) + Test (`VeloxDev.Core.Test/MVVM/` 22 files) | QS ✓ / API ✓ / SE ✓ |
| 03 | transition | `VeloxDev.Core` (`TransitionSystem/`) + 7 adapters | Demo (`Examples/Transition/*` 7 platforms + `AUTO TEST` conformance harness) + Test (`VeloxDev.Core.Test/TransitionSystem/` 28 files) | QS ✓ / API ✓ / SE ✓ |
| 04 | dynamic-theme | `VeloxDev.Core` (`DynamicTheme/`) + adapters | Demo (`Examples/Theme/*`) + Test (`VeloxDev.Core.Test/DynamicTheme/` 2 files) | QS ✓ / API ✓ / SE ✓ |
| 05 | aop | `VeloxDev.Core` (`AspectOriented/`, `#if NET`) | Demo (`Examples/AOP/WPF`, `Examples/AOP/Avalonia`) — **no unit tests** | QS ✓ / API ✓ / SE ✓ |
| 06 | **tickable** *(was `monobehaviour`)* | `VeloxDev.Core` (`TimeLine/`, `Interfaces/Tickable/`) | Demo (`Examples/Tickable/WPF`) + Test (`VeloxDev.Core.Test/TimeLine/` 4 files) | QS ✓ / API ✓ / SE ✓ |
| 07 | weak-types | `VeloxDev.Core` (`WeakTypes/`) | Test only (`VeloxDev.Core.Test/WeakTypes/` 4 files) — **no demo** | QS ✓ / API ✓ / SE ✓ |
| 08 | platform-adapters | `Src/Adapters/VeloxDev.{WPF,Avalonia,WinUI,MAUI,WinForms,Razor,Jalium}` + `Src/Templates` | Demo (`Examples/Workflow/<Platform>`, `Examples/Transition/<Platform>`) — per-platform detail partly *inferred* | QS ✓ / API ✓ / SE ✓ |
| 09 | **serialization** | `VeloxDev.Core` (`Serialization/`) + `VeloxDev.Core.Extension` (`CompiledGraphEx`, `CheckpointEx`, `FileCheckpointStore`) | Demo (the demos' save/load path through `TreeViewModel.Save`) + Test (`VeloxDev.Core.Test/Serialization/` 10 files, `VeloxDev.Core.Extension.Test/Serialization/` 32 files) | QS ✓ / API ✓ / SE ✓ |

## Feature → Directory Name Map (frozen)

| # | EN directory | ZH directory |
|---|---|---|
| 00 | `00_workflow-system` | `00_工作流系统` |
| 01 | `01_workflow-agent` | `01_工作流代理` |
| 02 | `02_mvvm` | `02_MVVM` |
| 03 | `03_transition` | `03_过渡动画` |
| 04 | `04_dynamic-theme` | `04_动态主题` |
| 05 | `05_aop` | `05_AOP` |
| 06 | `06_tickable` | `06_Tickable` |
| 07 | `07_weak-types` | `07_弱引用类型` |
| 08 | `08_platform-adapters` | `08_平台适配器` |
| 09 | `09_serialization` | `09_序列化` |

> Cross-dimension rule: the SAME name is used in `1_QuickStart`, `2_API`, and `3_SE_Analysis` feature sub-directories.
> **2026-10-01 change: `06_monobehaviour` → `06_tickable` / `06_MonoBehaviour` → `06_Tickable`.** Entries 00–05 and 07–08 unchanged.
> **2026-10-05 change: `09_serialization` added.** Serialization was previously a sub-topic of `00_workflow-system` (`2_API/00_workflow-system/03_mvvm-serialization`, `1_QuickStart/00_workflow-system/06_serialization`). It is now its own feature because it archives **any** view model — the workflow tree is one caller — and it owns a top-level source directory (`Src/Core/VeloxDev.Core/Serialization/`) alongside `WorkflowSystem/`. The API page moved to `2_API/09_serialization`; the QuickStart narrative step 06 **stays** in `00_workflow-system` (it is how you persist the tree that story just built). The freed `03` slot in `2_API/00_workflow-system/` was closed by renumbering `04`→`03`, `05`→`04`, `06`→`05` in both languages.

## Decisions taken during discovery

1. **`VeloxDev.Timing` is not a feature.** (`Src/Core/VeloxDev.Core/Timing/` + `Interfaces/Timing/`, first added 2026-09-14) It is keyword-level *infrastructure* shared by transition / dynamic-theme / tickable, not a user-facing capability. It is documented as a sub-module **under `03_transition`**, and referenced from `04` and `06`. (`TickManager.Bus` exposes the channel's `ITimeSourceControl`.) — Note: this is a different question from serialization, which **was** promoted to `09` on 2026-10-05 (see the map note above).
2. **`platform-adapters` keeps its `*inferred*` labelling** where demos do not exercise the detail.
3. The wiki's existing **localized top-level dimension names** (`0_欢迎` / `1_快速开始` / `3_SE分析` / `4_版权`) are **preserved** — the skill's Review step must not treat them as untracked entries to prune.

## What changed since the 2026-09-07 generation

| Feature | Change |
|---|---|
| workflow-system | **A whole new layer.** `CompilerEx/Runtime/Contracts` (`IExecutionCheckpointStore`, `IExecutionCompensation`, `IExecutionErrorSink`, `IExecutionGate`, `IExecutionObserver`, `ILogWriter`, `INodeRetryPolicy`, `RunOutcome`) + `Runtime/Model` implementations + `BranchRuntimeContext`, all **first added 2026-09-27**. `RuntimeContext` gained `Target`/`TargetReached`/`RedirectRequested`/`EndedWithError`/`MaxParallelBranches`/`ErrorSink`/`Compensation`/`CheckpointStore`/`Observer`/`RetryPolicy`/`ExecutionGate`/`LogWriter`/`MaxRetainedLogs` and `SnapshotLogs()`. `Compile/Model` gained `CompiledOutline`, `CompileKeyNormalizer`. |
| workflow-agent | 66 tools (README says "60+"). New subsystems: `Skills/`, `SubAgents/`, `Pipelines/`, `Dashboard/`, `MCP/`. New run-handle family: `StartCompiledWorkflow` / `ContinueCompiledWorkflow` / `GetCompiledRunStatus` / `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`. `PauseCompiledRun`/`ResumeCompiledRun` now **error** when the host brought its own execution gate. |
| mvvm | +2 interfaces (`IVeloxCommandCompletion`, `IVeloxCommandStatus`), +3 types (`CommandOutcome`, `CommandCompletion`, `VeloxCommandExtensions`). `VeloxCommand` gained `ExecuteAndWaitAsync`, `EventContext`, `IsBusy`/`ActiveCount`/`PendingCount`, `static HandlerException`, `IDisposable`, ValueTask factories (`#if` guarded). `UnLock` → `Unlock`. `CommandEventArgs.Cts` and the completion plumbing are now **`internal`**. Generator accepts `ValueTask`/`ValueTask<T>` and a single typed parameter, and reports **`VELOXCMD001`** for unsupported signatures. |
| tickable | Full rename; namespace `VeloxDev.TimeLine` unchanged. |
| transition / dynamic-theme | Now built on `VeloxDev.Timing`. |

## Coverage Reconciliation Matrix (step 8)

| Feature | Evidence | QuickStart | API | SE Analysis | Status |
|---|---|---|---|---|---|
| workflow-system | Demo + Test | ✅ | ✅ | ✅ | PASS |
| workflow-agent | Demo + Test | ✅ | ✅ | ✅ | PASS |
| mvvm | Demo + Test | ✅ | ✅ | ✅ | PASS |
| transition | Demo + Test | ✅ | ✅ | ✅ | PASS |
| dynamic-theme | Demo + Test | ✅ | ✅ | ✅ | PASS |
| aop | Demo | ✅ | ✅ | ✅ | PASS |
| tickable | Demo + Test | ✅ | ✅ | ✅ | PASS |
| weak-types | Test | ✅ | ✅ | ✅ | PASS |
| platform-adapters | Demo + Source | ✅ | ✅ | ✅ | PASS (residual) |

**Residual (platform-adapters only):** the per-adapter detail is marked *inferred* wherever no demo exercises it,
because no single demo covers every adapter's surface. Every other dimension of that feature is Demo/Test-backed.

No feature carries `TODO`. No Demo/Test feature has a ❌, so the quality gate passes.

## Review record — 2026-10-01

### Gates run (all zero errors)

| Gate | Command | Result |
|---|---|---|
| Structure | `python scripts/validate-structure.py` | 0 errors, 0 warnings |
| Titles | `python scripts/validate-titles.py` | 0 errors, 0 warnings |
| Links | `python scripts/validate-links.py` | 0 errors |
| Plot | `python scripts/validate-plot.py` | 0 errors, 0 warnings |
| KaTeX (real renderer) | `node scripts/validate-katex.js content` | 1454 expressions, 0 errors |
| Mermaid (real parser) | `node scripts/validate-mermaid.js content` | 55 blocks, 0 errors |
| PlantUML (real engine) | `python scripts/validate-plantuml.py content --engine java --jar <plantuml.jar>` | 115 blocks, 0 errors |
| Navigation | `python scripts/gen_tree.py --strict` | 0 directories missing index.md |
| Build | `dotnet build src/CloudGlyph/CloudGlyph.csproj` | 0 warnings, 0 errors |

### Code-authenticity audit

Every code claim in the English tree was audited against `Src/` and `Examples/`, one agent per feature group.
Findings were re-verified against source before any edit, and every fix was applied to both trees.

| Feature | Defects found | Representative examples |
|---|---|---|
| workflow-system | 26 | residual `[MonoBehaviour(...)]` / `InitializeMonoBehaviour()` left by the tickable rename; `WorkflowSpatialEx.cs` cited at a path that does not exist; `Error()` and `Warn()` conflated as redirect requests |
| workflow-agent | 22 | `MoveNode` documented as dispatching `SetAnchorCommand` when it deliberately dispatches `MoveCommand`; two wait helpers that do not exist; a tool total of 66 contradicting its own 68-item list |
| transition | 10 | eased time described as clamped when it is deliberately unclamped; Razor credited with a generic `Property<TValue>` it does not declare; `SetRate(0)` described as a pause |
| aop / tickable / weak-types / platform-adapters | 17 | `CloseTickable` claimed absent when `ITickable` declares it; wrong async-loop default TFM split; `TickManager` surface miscounted |
| mvvm / dynamic-theme | 3 | a test-file count of 22 where the directory holds 20; "four `TriggerAttributes`" where the array has ten |

Also corrected: the seeded tree's stale `title-allowlist.json` entries for the removed `MonoBehaviour*` types,
replaced with the `Tickable*` names, the `VeloxDev.AI.{Skills,Pipelines,Dashboard}` namespaces and `VeloxDev.Timing`.

### One audit finding was rejected

The tickable audit concluded that the recorded test run (`--filter "FullyQualifiedName~TimeLine"` → 46 passed)
could not be genuine, because only 31 `[TestMethod]`s live in `Src/Core/VeloxDev.Core.Test/TimeLine/`. The claim
was re-run: the filter is a **substring** match on the fully-qualified name, so it also selects 15 timing and
TransitionSystem tests whose method name contains `Timeline` (`Timeline_*`, `SharedTimeline_*`,
`Switch_EveryTargetIsAnchoredToTheSameTimeline`). 31 + 15 = 46, and the suite was executed again on 2026-10-01:
`已通过! - 失败: 0，通过: 46，已跳过: 0，总计: 46`. The original declaration was right and was restored; the
page now also explains why the filter over-matches.

### Known limits of this pass

- The authenticity audit covered the **English** tree. The Chinese tree was corrected in step with every fix,
  but its prose has not been independently audited.
- The demo-coverage pre-check was satisfied by the per-page evidence citations and the recorded run
  declarations; no exhaustive per-demo-file sweep was performed.

## API points that MUST be documented correctly

- `CommandEventArgs.Cts`, `TakeCts()`, `Completion`, `TryMarkCancelReported()`, `Complete()` are **`internal`** — not part of the public surface.
- `FrameEventArgs` setters (`DeltaTime`/`TotalTime`/`CurrentFPS`/`TargetFPS`) are **`internal`**.
- `CommandOutcome.Refused` deliberately has **no** `CommandEventType` counterpart — refusal is observable only through `ExecuteAndWaitAsync`.
- `TickManager.LoopChannel`, `BehaviorWrapper`, `ObjectPool<T>`, `GetOrCreateChannel` are **private**.
- The `CreateTaskOnlyWithValueTask*` factories exist only under `#if !NETSTANDARD2_0 && !NETFRAMEWORK`.
