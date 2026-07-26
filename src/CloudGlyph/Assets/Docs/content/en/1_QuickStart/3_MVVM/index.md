# MVVM — Quick Start

VeloxDev MVVM provides `VeloxCommand` (async command with semaphore) and `VeloxProperty` (source-generated observable properties).

## VeloxCommand

```csharp
using VeloxDev.MVVM;

// Basic async command
var cmd = new VeloxCommand(() => DoWork());

// With parameter and cancellation
var cmd2 = new VeloxCommand(async (param, ct) => {
	await Task.Delay(100, ct);
});

// With canExecute predicate and concurrency limit
var cmd3 = new VeloxCommand(
	async (param, ct) => await DoWorkAsync(param, ct),
	canExecute: p => p is string,
	semaphore: 2);

// Events
cmd.Started += (s, e) => UpdateUI();
cmd.Completed += (s, e) => UpdateUI();
cmd.Failed += (s, e) => HandleError(e);
```

## VeloxProperty (Source Generator)

```csharp
using VeloxDev.MVVM;

public partial class MyViewModel
{
	[VeloxProperty] private string name = string.Empty;
	[VeloxProperty] private int count = 0;
	[VeloxProperty] private bool isBusy = false;
	[VeloxProperty] private ObservableCollection<string> items = [];
}

// Generator produces observable properties with INotifyPropertyChanged
// Usage:
var vm = new MyViewModel();
vm.Name = "Hello";  // Triggers PropertyChanged
```

## VeloxCommand (Source Generator)

```csharp
public partial class MyViewModel
{
	[VeloxCommand]
	private async Task SaveAsync(object? parameter, CancellationToken ct)
	{
		// Generator creates SaveCommand property
	}
}

// Usage:
vm.SaveCommand.Execute(null);
```
