# MVVM — 快速入门

VeloxDev MVVM 提供 VeloxCommand（带信号量的异步命令）和 VeloxProperty（源生成的可观察属性）。

## VeloxCommand

`csharp
using VeloxDev.MVVM;

var cmd = new VeloxCommand(() => DoWork());
var cmd2 = new VeloxCommand(async (param, ct) => {
	await Task.Delay(100, ct);
});
var cmd3 = new VeloxCommand(
	async (param, ct) => await DoWorkAsync(param, ct),
	canExecute: p => p is string,
	semaphore: 2);

cmd.Started += (s, e) => UpdateUI();
cmd.Completed += (s, e) => UpdateUI();
`

## VeloxProperty (源生成器)

`csharp
public partial class MyViewModel
{
	[VeloxProperty] private string name = string.Empty;
	[VeloxProperty] private int count = 0;
	[VeloxProperty] private bool isBusy = false;
}
// 生成器生成: public string Name { get; set; } + INotifyPropertyChanged
`
