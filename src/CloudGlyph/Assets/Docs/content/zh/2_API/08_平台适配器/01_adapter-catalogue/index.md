# API — 适配器目录

每个适配器包都提供相同的三个核心命名空间（有主题接线的则提供四个）。本页是按适配器的索引；共享工作流行为的**形态**见 [00_attached-behaviors](../00_attached-behaviors/index.md)，各适配器**过渡/主题成员**记录于过渡动画与动态主题特性。

## 各适配器表面

| 适配器 | 提供的命名空间 | 工作流行为文件（`Attached/Workflow/*`） |
|---|---|---|
| WPF | `AttachedBehaviors`、`TransitionSystem`、`DynamicTheme`、`Adapters.NativeSamplers` | `WorkflowSurfaceBehavior`、`WorkflowCanvasTransformBehavior`、`ViewPool`、`ViewManager`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`、`WorkflowMinimapOverlay` |
| Avalonia | 同上四个 | WPF 集合 **加** `PlatformDetection`（internal，触屏平台检测） |
| WinUI | 同上四个 | WPF 集合 |
| MAUI | 同上四个 | WPF 集合 **减** `WorkflowCanvasTransformBehavior`；**加** `WorkflowLinkOverlay` |
| WinForms | 同上四个 | WPF 集合 **加** `NativeWindowStyleHelper`（internal）；`ViewManager.cs` 另声明 `IWorkflowTemplateSelector` |
| Razor | 同上四个 | 组件集合：`WorkflowSurfaceBehavior`、`ViewPool`、`WorkflowGridDecorator`、`WorkflowMinimapOverlay`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`（`.razor` 分部类）**加** 静态 `WorkflowCanvasTransformBehavior`、`WorkflowGeometryScope`、`WorkflowRuntimeIds` |
| Jalium | `AttachedBehaviors`、`TransitionSystem`、`Adapters.NativeSamplers`（**无 `DynamicTheme`**） | WPF 集合 **加** `WorkflowGridDecorator`、`WorkflowTreeView` 与 `IWorkflowTemplateSelector` |

### 各适配器的类形态

**相同公共名**对应不同框架基类型；各行为的成员表见对应形态页。简表如下：

| 行为 | WPF | WinUI | Jalium | Avalonia | MAUI | WinForms | Razor |
|---|---|---|---|---|---|---|---|
| `WorkflowSurfaceBehavior` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : AvaloniaObject` | `sealed`（附加 `BindableProperty`） | `sealed`（状态表） | `ComponentBase` |
| `ViewPool` | `sealed : DependencyObject` | `sealed : DependencyObject` | `static class` | `sealed : AvaloniaObject` | `sealed`（附加 `BindableProperty`） | `sealed`（状态表） | `ComponentBase` |
| `ViewManager` 构造 | `(Panel)` | `(Panel)` | `(Panel)` ： `IDisposable` | `(Panel, IDataTemplate?)` | `(Layout)` | `(Control)` ： `IDisposable` | 无（组件） |
| 节点/槽行为 | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : DependencyObject` | `sealed : AvaloniaObject` | `sealed`（附加 `BindableProperty`） | `sealed`（状态表） | `ComponentBase` |
| `WorkflowMinimapOverlay` | `FrameworkElement` | `Canvas` | `FrameworkElement` | `Control` | `GraphicsView : IDrawable` | `static class`（绘制控件） | `ComponentBase` |
| `WorkflowCanvasTransformBehavior` | 静态（附加 DP） | 静态（附加 DP） | 静态（附加 DP） | `sealed : AvaloniaObject` | 不提供 | 静态（持有 `Offset`） | 静态（CSS） |

## 各适配器过渡接线（摘要）

每个适配器在 `VeloxDev.TransitionSystem` 中提供完整适配器表面：`Transition`、`Transition<T>`、`Transition<T>.StateSnapshot`、`TransitionEx`、`Interpolator`、`TransitionEffect`、`TransitionEffects`、`State`、`UIThreadInspector`、`TransitionScheduler`、`TransitionInterpreter`，外加 `VeloxDev.Adapters.NativeSamplers` 里的平台采样器。成员记录于过渡动画特性（`2_API/03_transition` 的 `03_adapter-provided` 一节）。

| 适配器 | 是否带优先级 | 注册的采样器（`Interpolator` 静态构造） |
|---|---|---|
| WPF | `DispatcherPriority`（`Render`） | 画刷/几何类：`BrushSampler`、`ThicknessSampler`、`PointSampler`、`CornerRadiusSampler`、`TransformSampler`、`SizeSampler`、`RectSampler`、`VectorSampler`、`ColorSampler`、`DropShadowEffectSampler`、`Point3DSampler`、`Vector3DSampler` |
| Avalonia | `DispatcherPriority` | Avalonia 值类型（`BrushSampler`、`ThicknessSampler`、`PixelPointSampler`、`BoxShadowsSampler`、`GridLengthSampler`、……） |
| WinUI | `DispatcherQueuePriority`（`High`） | WinUI 类型（`ProjectionSampler`、`GridLengthSampler`、……） |
| MAUI | 无优先级 | MAUI 类型（`PointFSampler`、`RectFSampler`、`SizeFSampler`、`ShadowSampler`、……） |
| WinForms | 无优先级 | `PaddingSampler` |
| Razor | 无优先级 | `StringSampler` |
| Jalium | `DispatcherPriority` | Jalium 类型含 `Transform3DSampler` |

## 各适配器主题接线（摘要）

主题值转换器位于各适配器程序集的 `VeloxDev.DynamicTheme`（**Jalium 除外**，它不提供 DynamicTheme 层）。转换器完整语义记录于动态主题特性（`2_API/04_dynamic-theme` 的 `04_PlatformAdapters` 一页）。

| 适配器 | 转换器集合 |
|---|---|
| WPF / Avalonia / WinUI / MAUI | 七个：`BrushConverter`、`ColorConverter`、`CornerRadiusConverter`、`DoubleConverter`、`ObjectConverter`、`PointConverter`、`ThicknessConverter` |
| WinForms | 十三个：`DoubleConverter`、`IntConverter`、`FloatConverter`、`PointConverter`、`PointFConverter`、`SizeConverter`、`SizeFConverter`、`RectangleConverter`、`RectangleFConverter`、`PaddingConverter`、`ColorConverter`、`FontConverter`、`ObjectConverter` |
| Razor | 四个：`DoubleConverter`、`StringConverter`、`IntConverter`、`BoolConverter` |
| Jalium | 无 |
