# MVVM — `MVVM`

Registers source output for every `partial` class and produces one file per class containing: the `PropertyChanging` / `PropertyChanged` events and `OnPropertyChanging(string)` / `OnPropertyChanged(string)` methods (when no base provides them), an `OnCollectionChanged<T>` stub (for collection properties), the observable property implementations, and the `partial void OnXxxChanging/OnXxxChanged` plus collection partials.

It also adapts to a host MVVM framework: `MVVMWriter.DetectSetterMode` (`MVVMWriter.cs`, lines 42-89) detects CommunityToolkit.Mvvm (`[ObservableObject]`), Prism (`SetProperty(ref T, T, string)`), ReactiveUI (`IReactiveObject`), and Caliburn.Micro (`NotifyOfPropertyChange(string)`), and delegates the generated setter to that framework's notification method instead of raising events itself.
