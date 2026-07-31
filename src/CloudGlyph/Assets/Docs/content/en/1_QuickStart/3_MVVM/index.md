# MVVM — Quick Start

VeloxDev MVVM generates observable properties and async commands at compile time. A `[VeloxProperty]` on a private field (or a partial property) is expanded by the Roslyn source generator into a public property that raises `INotifyPropertyChanging` / `INotifyPropertyChanged` and exposes `partial void` hooks. A `[VeloxCommand]` on a `Task`/`void` method is expanded into a lazily created `IVeloxCommand` property wired to that method.

#### 1. Install / Add Dependency

Add the core package to any WPF / Avalonia / WinUI / MAUI project:

```bash
dotnet add package VeloxDev.Core
```

The generator ships transitively — `VeloxDev.Core.csproj` references `VeloxDev.Core.Generator` (Src/Core/VeloxDev.Core/VeloxDev.Core.csproj, lines 26-29):

```xml
<ItemGroup>
    <PackageReference Include="VeloxDev.Core.Generator" Version="6.0.82" />
</ItemGroup>
```

No manual wiring is required. Demo view-models are plain `partial` classes deriving from a local `ObservableViewModelBase`; the generator only requires the class to be `partial`.

#### 2. Declare Properties

Annotate a private field with `[VeloxProperty]`; the generator creates a public property named after the field (underscore stripped, first letter upper-cased). From the WPF demo (Examples/MVVM/WPF/Demo/MainWindowViewModel.cs, lines 23-30):

```csharp
/* 快速生成你的属性 */
[VeloxProperty] private int _index = 0;
[VeloxProperty] private string _greeting = $"current index: 0";
[VeloxProperty] private ObservableCollection<string> _items = [];
[VeloxProperty] private string? _selectedItem;
[VeloxProperty] private string _selectedItemSummary = "当前选中: (无)";
[VeloxProperty] private string _collectionStatus = "等待集合通知";
[VeloxProperty] private string _collectionTrace = "OnCollectionChanged<T> 尚未触发";
```

For a setter, the generator also declares `partial void OnXxxChanging(old, new)` / `OnXxxChanged(old, new)` hooks. Implement them anywhere in the partial class; the demo reacts to `Index` by refreshing a command (lines 33-36):

```csharp
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // 通知 MinusCommand 的可执行性需要更新
}
```

#### 3. Declare Commands

Annotate a `Task` (or `void`) method with `[VeloxCommand]`. The generator creates an `IVeloxCommand` property named `<MethodName>Command`; `name: "Auto"` strips a trailing `Async` suffix. From the demo (lines 60-80):

```csharp
/* 一个默认的 Command，名字自动截取，无可用性验证，排队执行 */
[VeloxCommand(name: "Auto", canValidate: false, semaphore: 1)]
private Task Plus(object? sender, CancellationToken ct)
{
    Index++;
    Greeting = $"current index: {Index}";
    return Task.CompletedTask;
}

/* 开启可用性验证 */
[VeloxCommand(canValidate: true)]
private Task Minus(object? sender, CancellationToken ct)
{
    Index--;
    Greeting = $"current index: {Index}";
    return Task.CompletedTask;
}
/* 此时必须实现此分部方法 */
private partial bool CanExecuteMinusCommand(object? parameter)
{
    return _index > 0;
}
```

`canValidate: true` requires the `private partial bool CanExecute<Name>Command(object? parameter)` implementation. The factory is chosen from the method signature: two parameters / none map to the primary `VeloxCommand` constructor, a single `object?` maps to `CreateTaskOnlyWithParameter`, a single `CancellationToken` maps to `CreateTaskOnlyWithCancellationToken` (Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs, lines 78-116). The XAML layer binds directly to the generated command (`MainWindow.xaml`, lines 18-19):

```xml
<Button Content="增加" Command="{Binding PlusCommand}" Margin="0,0,12,0" Padding="16,6"/>
<Button Content="减少" Command="{Binding MinusCommand}" Padding="16,6"/>
```

#### 4. Collection Tracking

A `[VeloxProperty]` whose type implements `INotifyCollectionChanged` (e.g. `ObservableCollection<T>`) gets extra generated members: an `OnXxxCollectionChanged` handler, forwarding to `OnCollectionChanged<T>`, and four item partials — `OnItemAddedToXxx`, `OnItemRemovedFromXxx`, `OnItemMovedInXxx`, `OnItemsResetInXxx`. The generated getter calls `ObservableCollectionTracker.EnsureSubscribed` on every access but only subscribes once (Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs, lines 444-464). The demo implements the item hooks (lines 178-195):

```csharp
partial void OnItemAddedToItems(IEnumerable<string> items)
{
    var materialized = items.ToArray();
    CollectionStatus = $"新增 {materialized.Length} 项: {FormatItems(materialized)} | 当前总数: {Items.Count}";
    RefreshCollectionCommands();
}

partial void OnItemRemovedFromItems(IEnumerable<string> items)
{
    var materialized = items.ToArray();
    if (SelectedItem is not null && !Items.Contains(SelectedItem))
    {
        SelectedItem = Items.FirstOrDefault();
    }

    CollectionStatus = $"移除 {materialized.Length} 项: {FormatItems(materialized)} | 当前总数: {Items.Count}";
    RefreshCollectionCommands();
}
```

The base class forwards every raw `CollectionChanged` (override at lines 54-57):

```csharp
protected override void OnCollectionChanged<T>(string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)
{
    CollectionTrace = $"{propertyName}: {e.Action} | old=[{FormatItems(oldItems)}] | new=[{FormatItems(newItems)}]";
}
```

#### 5. Command Lifecycle Control

`IVeloxCommand` exposes `Lock` / `UnLock` (block new triggers without interrupting the running instance), `Interrupt` (cancel the current invocation) and `Clear` (cancel current + queued). Fire-and-forget form (lines 157-165):

```csharp
/* 无阻中断 */
private void FreeCommand()
{
    MinusCommand.Lock();   // 进入锁定状态，阻止新的命令触发但不会中断当前执行中的命令

    MinusCommand.Interrupt();    // 中断当前命令
    MinusCommand.Clear();        // 中断当前命令和正在排队的所有命令

    MinusCommand.UnLock(); // 解除锁定
}
```

Awaitable twins `InterruptAsync` / `ClearAsync` (lines 168-176):

```csharp
/* 可等待中断 */
private async Task FreeCommandAsync()
{
    MinusCommand.Lock();   // 进入锁定状态，阻止新的命令触发但不会中断当前执行中的命令

    await MinusCommand.InterruptAsync();    // 中断当前命令
    await MinusCommand.ClearAsync(); // 中断当前命令和正在排队的所有命令

    MinusCommand.UnLock(); // 解除锁定
}
```

#### 6. Host-Framework Coexistence

The MVVM generator detects the host MVVM framework and delegates its setter to that framework's notification method instead of raising `PropertyChanged` itself (Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs, `DetectSetterMode`, lines 42-89):

| Host framework | Detection | Generated setter uses |
|---|---|---|
| CommunityToolkit.Mvvm | `[ObservableObject]` attribute | `SetProperty(ref _name, value, nameof(Name))` |
| Prism | base with `SetProperty(ref T, T, string)` | `SetProperty(ref _name, value, nameof(Name))` |
| ReactiveUI | `IReactiveObject` | `RaiseAndSetIfChanged(ref _name, value, nameof(Name))` |
| Caliburn.Micro | `NotifyOfPropertyChange(string)` | field assignment + `NotifyOfPropertyChange(nameof(Name))` |

*The table is inferred from `DetectSetterMode`; the shipped demos derive from the local `ObservableViewModelBase`, not a framework base.* The Avalonia demo carries the `CommunityToolkit.Mvvm` package (Examples/MVVM/Avalonia/Demo/Demo.csproj, line 26) so a host framework can coexist.

#### 7. Verification

Build and run the demo. Set a breakpoint in `OnIndexChanging` / `OnIndexChanged`, click 增加 (Plus) / 减少 (Minus), and observe `PropertyChanging` → field assignment → `OnXxxChanged` → `PropertyChanged`. With `_index == 0` the 减少 button is disabled because `CanExecuteMinusCommand` returns false; `MinusCommand.Notify()` from `OnIndexChanged` re-queries it after each change.

#### 8. Complete Code

The full annotated sample lives in the demo projects:

- WPF: `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, `ObservableViewModelBase.cs`, `MainWindow.xaml`
- Avalonia: `Examples/MVVM/Avalonia/Demo/ViewModels/MainWindowViewModel.cs`, `ViewModels/ObservableViewModelBase.cs`
