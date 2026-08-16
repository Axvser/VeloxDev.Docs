# VeloxDev — Feature Inventory

> Working artifact produced by the `cloud-glyph-wiki-create` skill (module-discovery step).
> The feature set is **FROZEN** after discovery. Steps 3–5 only mark the Coverage Status column;
> they never add, remove, or rename features.
> Regenerated each run — a future template sync removing it is expected.

## Feature Inventory

| Feature | Owning Project | Public API Surface | Dependencies | Evidence | Coverage Status |
|---|---|---|---|---|---|
| workflow-system (工作流系统) | `VeloxDev.Core` (+ `VeloxDev.Core.Extension` for `ComponentModelEx` serialization) | `[WorkflowBuilder.Tree/Node/Slot/Link<T>]`; interfaces `IWorkflowViewModel`, `IWorkflowTreeViewModel(Helper)`, `IWorkflowNodeViewModel(Helper)`, `IWorkflowSlotViewModel(Helper)`, `IWorkflowLinkViewModel(Helper)`, `IWorkflowActionPair`, `IWorkflowIdentifiable`, `ISlotProvider`, `ISpatialMap`, `ISpatialBoundsProvider`; value types `Anchor`, `Size`, `Offset`, `Viewport`, `CanvasLayout`, `CellKey`, `TaskContext`, `WorkflowActionPair`; enums `SlotChannel`, `SlotState`; defaults `TreeDefaultViewModel`/`TreeHelper<T>` etc.; `SelectorEx` (`SlotEnumerator<T>`, `ConditionalSlot<T>`, `SlotDefinition`); `SpatialGridHashMap<T>`, `WorkflowSpatialManager`, `WorkflowSpatialEx`; `StandardEx` (`WorkflowTreeEx`, `WorkflowNodeEx`, `WorkflowSlotEx`, `WorkflowLinkEx`, `WorkflowCommandEx`); `CompilerEx` (`CompilerViewModel`, `CompiledGraph`, `ActionEntry`/`ExecuteEntry`/`BranchEntry`/`ParallelEntry`, `BranchOption`, `CompilerEngine`, `CompileContext`, `RuntimeContext`, `ICompileTimeRouter`, `IRedirectable`, `ICompileTimeAware`, `IRuntimeAware`, `ICompileContext`, `IRuntimeContext`, `RouterCompileMode`); `VeloxDev.MVVM.Serialization.ComponentModelEx` | Roslyn source generator (`VeloxDev.Core.Generator`); no third-party runtime deps | **Demo** (`Examples/Workflow/*`) + **Test** (`VeloxDev.Core.Test/WorkflowSystem`, `VeloxDev.Core.Extension.Test/.../Functions`) | QS ✓ / API ✓ / SE ✓ |
| workflow-agent (工作流代理) | `VeloxDev.Core.Extension` (+ `VeloxDev.Core` AI utilities) | `AgentEx.AsAIAgent` / `tree.AsAgentScope()` → `WorkflowAgentScope` (fluent `With*`); `WorkflowAgentToolkit` (~60 `AITool`s, groups: query / mutation / state-diff / slot-collection / traversal / connection / bulk / layout / analytics / composite / interaction); `WorkflowStateTracker` (JSON diffs); `McpScope`, `McpServerConfiguration`, `McpServerRunMode`, `McpServerStatus`; `VeloxDev.AI` (`AgentContextAttribute`, `AgentCommandParameterAttribute`, `SlotSelectorsAttribute`, `AgentLanguages`, `AgentContextReader`, `AgentCommandDiscoverer`, `AgentMethodInvoker`, `AgentPropertyAccessor`, `AgentTypeResolver`, `AgentSelectionEventArgs`, `AgentConfirmationEventArgs`, `AgentConfirmationResult`, `AgentToolCallEventArgs`) | `Microsoft.Extensions.AI` (`AITool`, `ChatClient`), `ModelContextProtocol` | **Test** (`VeloxDev.Core.Extension.Test/Agent/*`, `VeloxDev.Core.Test/AI/*`) + README + Demo agent pane (`Examples/Workflow/WinForms`) | QS ✓ / API ✓ / SE ✓ |
| mvvm (MVVM) | `VeloxDev.Core` | `VeloxPropertyAttribute`, `VeloxCommandAttribute`, `IVeloxCommand`, `VeloxCommand` (+ static factories), `CommandEventArgs`, `CommandEventType`, `CommandEventHandler`, `ObservableCollectionTracker`; generator `VeloxDev.Generators.MVVM` / `.Command` | Roslyn source generator | **Demo** (`Examples/MVVM/WPF`, `Examples/MVVM/Avalonia`) + **Test** (`VeloxDev.Core.Test/MVVM/VeloxCommandTests.cs`) | QS ✓ / API ✓ / SE ✓ |
| transition (过渡动画) | `VeloxDev.Core` + all six adapters | `IInterpolable`, `IValueInterpolator`, `IEaseCalculator`, `ITransitionProperty`, `IFrameState`, `ITransitionEffectCore`, `ITransitionEffect<TPriorityCore>`, `ITransitionSchedulerCore`, `ITransitionInterpreterCore`, `IUIThreadInspectorCore`, frame-pump interfaces (`IFrameInterpolatorCore`, `IFrameSequenceCore`, …); enum `RotationDirection`; static `Eases` (+ concrete `Ease*`); `Transition`/`Transition<T>`, `StateSnapshotCore`, `StateCore`, `InterpolatorCore`, `TransitionEffectCore`, `TransitionSchedulerCore`, `TransitionInterpreterCore`, `InterpolatorOutputBase`, `TransitionProperty`, `TransitionSnapshotHelper`; native interpolators (`NativeInterpolators/*`); `TransitionEx`; adapter types (`Interpolator`, `TransitionEffect`, `TransitionEffects`, `UIThreadInspector`, per-platform `StateSnapshot.Property` overloads) | `System.Numerics`, `System.Drawing` (netstandard2.0-guarded) | **Demo** (`Examples/Transition/*`) + **Test** (`VeloxDev.Core.Test/TransitionSystem/*`) | QS ✓ / API ✓ / SE ✓ |
| dynamic-theme (动态主题) | `VeloxDev.Core` + adapters | `ThemeManager` (static: `Current`, `StartModel`, `SetPlatformInterpolator`, `SetCurrent`, `Register/Unregister`, `Transition<T>`, `Jump<T>`), `ThemeCache`, `ThemeConfigAttribute<TConverter, TTheme...>` (6 arities), enum `StartModel`, `Dark`/`Light`, `ITheme`, `IThemeObject`, `IThemeValueConverter`, platform converters (`BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter`) | `VeloxDev.Core` TransitionSystem engine + adapter `Interpolator` | **Demo** (`Examples/Theme/*`) + **Test** (`VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`) | QS ✓ / API ✓ / SE ✓ |
| aop (AOP) | `VeloxDev.Core` (`#if NET`) | `AspectOrientedAttribute`, `IAspectOriented`, enum `ProxyMembers`, delegate `ProxyHandler`, static `ProxyEx` (`CreateProxy`, `SetProxy`), `ProxyInstance : DispatchProxy`, static `Aop` (`Map`, `GetTarget`), `AopCache.Resolve<TClass,TInterface>`; generated `{Class}_{Ns}_Aop` interface + `Aop(this T)` extension | `System.Reflection.DispatchProxy`; Roslyn source generator | **Demo** (`Examples/AOP/*`) + **Test** (AOP tests under `VeloxDev.Core.Test`) | QS ✓ / API ✓ / SE ✓ |
| monobehaviour (MonoBehaviour) | `VeloxDev.Core` | `MonoBehaviourAttribute(channel, fps)`, static `MonoBehaviourManager` (lifecycle: `Start/StopAsync/Pause/Resume/RestartAsync/TogglePause`; registration: `RegisterBehaviour/UnregisterBehaviour/SetTargetFPS/SetFixedUpdateInterval/SetTimeScale/ExecuteOnMainThread/SetUseAsyncLoop`; status: `IsRunning/IsPaused/CurrentFPS/TargetFPS/TotalTime/TotalFrames/ActiveBehaviorCount/SystemStatus`; events `OnChannel*`), `IMonoBehaviour`, `TimeLineEventArgs`, `FrameEventArgs`, `ThreadSafeFrameEventArgs`, `MonoBehaviourChannelEventArgs`, `TransitionEventArgs` | Roslyn source generator | **Demo** (`Examples/MonoBehaviour/WPF`) + **Test** (`VeloxDev.Core.Test/TimeLine/*`) | QS ✓ / API ✓ / SE ✓ |
| weak-types (弱引用类型) | `VeloxDev.Core` | `WeakDelegate<TDelegate>`, `WeakQueue<T>`, `WeakStack<T>`, `WeakCache<TTargetKey, TCacheKey>` | — | **Test** (`VeloxDev.Core.Test/WeakTypes/*`) | QS ✓ / API ✓ / SE ✓ |
| platform-adapters (平台适配器) | `VeloxDev.WPF` / `VeloxDev.Avalonia` / `VeloxDev.WinUI` / `VeloxDev.MAUI` / `VeloxDev.WinForms` / `VeloxDev.Razor` + `Src/Templates` | Attached workflow behaviors (`WorkflowSurfaceBehavior`, `WorkflowCanvasTransformBehavior`, `ViewPool`/`ViewManager`, `WorkflowNodeDragBehavior`, `WorkflowSlotConnectionBehavior`, `WorkflowSlotLayoutBehavior`, `WorkflowMinimapOverlay`, `IWorkflowGridDecorator`, `IWorkflowMinimapOverlay`) in `VeloxDev.WorkflowSystem.AttachedBehaviors`; per-platform Transition/Theme wiring (`Interpolator`, `TransitionEffect`, `TransitionEffects`, `UIThreadInspector`, `State`, `ThemeValueConverters`, `Interpolators/*`); `dotnet new` item templates (`*-v-node`, `*-v-slot`, `*-v-link`, `*-v-tree`, `*-v-selector`, `*-v-decorator`, `*-v-minimap`) | Per-framework SDK (`UseWPF`, `UseWinUI`, `UseMaui`, `UseWindowsForms`, Avalonia/Razor SDK) | README + **Demo** (workflow demos reference attached behaviors) + **Source** (per-platform detail largely *inferred* from source, not exercised in demos) | QS ✓ / API ✓ (partial — inferred) / SE ✓ |

## Feature → Directory Name Map (frozen)

| # | EN directory (QuickStart / API / SE feature sub-dirs) | ZH directory |
|---|---|---|
| 00 | `00_workflow-system` | `00_工作流系统` |
| 01 | `01_workflow-agent` | `01_工作流代理` |
| 02 | `02_mvvm` | `02_MVVM` |
| 03 | `03_transition` | `03_过渡动画` |
| 04 | `04_dynamic-theme` | `04_动态主题` |
| 05 | `05_aop` | `05_AOP` |
| 06 | `06_monobehaviour` | `06_MonoBehaviour` |
| 07 | `07_weak-types` | `07_弱引用类型` |
| 08 | `08_platform-adapters` | `08_平台适配器` |

> Cross-dimension rule: the SAME name is used in `1_QuickStart`, `2_API`, and `3_SE_Analysis` feature sub-directories.
> SE page-group overview dirs: `00_file-structure`, `01_functional-structure`, `02_design-patterns`, `03_data-flow`, `04_complexity`
> (ZH: `00_文件结构`, `01_功能结构`, `02_设计模式分析`, `03_数据流分析`, `04_复杂度分析`).

## Coverage Reconciliation Matrix (filled in step 8)

| Feature | Evidence | QuickStart | API | SE Analysis | Status |
|---|---|---|---|---|---|
| workflow-system | Demo + Test | ✅ | ✅ | ✅ | PASS |
| workflow-agent | Test + README + Demo | ✅ | ✅ | ✅ | PASS |
| mvvm | Demo + Test | ✅ | ✅ | ✅ | PASS |
| transition | Demo + Test | ✅ | ✅ | ✅ | PASS |
| dynamic-theme | Demo + Test | ✅ | ✅ | ✅ | PASS |
| aop | Demo + Test | ✅ | ✅ | ✅ | PASS |
| monobehaviour | Demo + Test | ✅ | ✅ | ✅ | PASS |
| weak-types | Test | ✅ | ✅ | ✅ | PASS |
| platform-adapters | README + Demo + Source | ✅ | ⚠️ partial — per-platform detail inferred from source, not exercised in demos | ✅ | RESIDUAL |

> Review (step 8) note: All Demo/Test-evidenced features are fully covered across the three dimensions (verified against the on-disk tree, not the stale status column). `platform-adapters` is the only residual: its per-platform API surface is largely *inferred* from source (marked as such on the QS and API pages), so the API page is partial by design. Reproducibility spot-check: `06_monobehaviour` and `07_weak-types` QuickStarts declare ✅ (built & ran 2026-08-17, recorded output present); the other seven QuickStarts declare ⚠️ (statically verified only).
