# MVVM — 快速入门

VeloxDev MVVM 在编译期生成可观察属性与异步命令。`[VeloxProperty]` 标记的私有字段（或 partial 属性）会被 Roslyn 源生成器展开为公开属性，触发 `INotifyPropertyChanging` / `INotifyPropertyChanged`，并提供 `partial void` 钩子。`[VeloxCommand]` 标记的 `Task`/`void` 方法会被展开为懒加载的 `IVeloxCommand` 属性并绑定到该方法。

#### 1. 安装 / 添加依赖

为任意 WPF / Avalonia / WinUI / MAUI 项目添加核心包：

```bash
dotnet add package VeloxDev.Core
```

生成器随包传递引用 — `VeloxDev.Core.csproj` 中引用了 `VeloxDev.Core.Generator`（Src/Core/VeloxDev.Core/VeloxDev.Core.csproj，第 26-29 行）：

```xml
<ItemGroup>
    <PackageReference Include="VeloxDev.Core.Generator" Version="6.0.82" />
</ItemGroup>
```

无需手动接线。示例中的 ViewModel 都是继承自本地 `ObservableViewModelBase` 的普通 `partial` 类；生成器只要求类是 `partial` 的。

#### 2. 声明属性

用 `[VeloxProperty]` 标记私有字段，生成器会创建与之对应的公开属性（去掉下划线并把首字母大写）。来自 WPF 示例（Examples/MVVM/WPF/Demo/MainWindowViewModel.cs，第 23-30 行）：

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

对于带 setter 的属性，生成器还会声明 `partial void OnXxxChanging(old, new)` / `OnXxxChanged(old, new)` 钩子。可在 partial 类中任意位置实现；示例在 `Index` 变化时刷新命令（第 33-36 行）：

```csharp
partial void OnIndexChanged(int oldValue, int newValue)
{
    MinusCommand.Notify(); // 通知 MinusCommand 的可执行性需要更新
}
```

#### 3. 声明命令

用 `[VeloxCommand]` 标记 `Task`（或 `void`）方法。生成器创建名为 `<方法名>Command` 的 `IVeloxCommand` 属性；`name: "Auto"` 会去掉 `Async` 后缀。来自示例（第 60-80 行）：

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

`canValidate: true` 要求实现 `private partial bool CanExecute<名称>Command(object? parameter)`。工厂方法按签名选择：两个参数/无参映射到主构造函数 `VeloxCommand`，单个 `object?` 映射到 `CreateTaskOnlyWithParameter`，单个 `CancellationToken` 映射到 `CreateTaskOnlyWithCancellationToken`（Src/Generators/VeloxDev.Core.Generator/Writers/CommandWriter.cs，第 78-116 行）。XAML 层直接绑定生成的命令（MainWindow.xaml，第 18-19 行）：

```xml
<Button Content="增加" Command="{Binding PlusCommand}" Margin="0,0,12,0" Padding="16,6"/>
<Button Content="减少" Command="{Binding MinusCommand}" Padding="16,6"/>
```

#### 4. 集合追踪

类型实现 `INotifyCollectionChanged`（例如 `ObservableCollection<T>`）的 `[VeloxProperty]` 会额外生成成员：`OnXxxCollectionChanged` 处理器、转发到 `OnCollectionChanged<T>` 的方法，以及四个项级 partial 钩子 — `OnItemAddedToXxx`、`OnItemRemovedFromXxx`、`OnItemMovedInXxx`、`OnItemsResetInXxx`。生成的 getter 每次访问都会调用 `ObservableCollectionTracker.EnsureSubscribed`，但只会订阅一次（Src/Generators/VeloxDev.Core.Generator/Base/Analizer.cs，第 444-464 行）。示例实现了项级钩子（第 178-195 行）：

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

基类转发每一条原始 `CollectionChanged`（重写于第 54-57 行）：

```csharp
protected override void OnCollectionChanged<T>(string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)
{
    CollectionTrace = $"{propertyName}: {e.Action} | old=[{FormatItems(oldItems)}] | new=[{FormatItems(newItems)}]";
}
```

#### 5. 命令生命周期控制

`IVeloxCommand` 提供 `Lock` / `UnLock`（阻止新触发但不会中断正在执行的命令）、`Interrupt`（中断当前调用）和 `Clear`（中断当前 + 所有排队调用）。一次性形式（第 157-165 行）：

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

可等待版本 `InterruptAsync` / `ClearAsync`（第 168-176 行）：

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

#### 6. 与宿主框架共存

MVVM 生成器会检测宿主 MVVM 框架，并让生成的 setter 委托给该框架自身的通知方法，而不是自行触发 `PropertyChanged`（Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs，`DetectSetterMode`，第 42-89 行）：

| 宿主框架 | 检测方式 | 生成的 setter 使用 |
|---|---|---|
| CommunityToolkit.Mvvm | `[ObservableObject]` 特性 | `SetProperty(ref _name, value, nameof(Name))` |
| Prism | 基类含 `SetProperty(ref T, T, string)` | `SetProperty(ref _name, value, nameof(Name))` |
| ReactiveUI | `IReactiveObject` | `RaiseAndSetIfChanged(ref _name, value, nameof(Name))` |
| Caliburn.Micro | `NotifyOfPropertyChange(string)` | 字段赋值 + `NotifyOfPropertyChange(nameof(Name))` |

*上表依据 `DetectSetterMode` 推断；随附示例均派生自本地 `ObservableViewModelBase`，并未使用框架基类。* Avalonia 示例引入了 `CommunityToolkit.Mvvm` 包（Examples/MVVM/Avalonia/Demo/Demo.csproj，第 26 行），说明宿主框架可以共存。

#### 7. 验证

编译并运行示例。在 `OnIndexChanging` / `OnIndexChanged` 处打断点，点击 增加（Plus）/ 减少（Minus），观察 `PropertyChanging` → 字段赋值 → `OnXxxChanged` → `PropertyChanged` 的顺序。当 `_index == 0` 时 减少 按钮被禁用，因为 `CanExecuteMinusCommand` 返回 false；`OnIndexChanged` 中的 `MinusCommand.Notify()` 会在每次变化后重新查询可执行性。

#### 8. 完整代码

完整带注释的示例位于示例项目中：

- WPF：`Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`、`ObservableViewModelBase.cs`、`MainWindow.xaml`
- Avalonia：`Examples/MVVM/Avalonia/Demo/ViewModels/MainWindowViewModel.cs`、`ViewModels/ObservableViewModelBase.cs`
