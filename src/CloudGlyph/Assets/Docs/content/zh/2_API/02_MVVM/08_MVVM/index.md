# MVVM — `MVVM`

为每个 `partial` 类注册源输出并每类产出一个文件，内容包含：`PropertyChanging` / `PropertyChanged` 事件与 `OnPropertyChanging(string)` / `OnPropertyChanged(string)` 方法（当基类未提供时）、集合属性的 `OnCollectionChanged<T>` 桩、可观察属性的实现，以及 `partial void OnXxxChanging/OnXxxChanged` 与集合 partial。

它还会适配宿主 MVVM 框架：`MVVMWriter.DetectSetterMode`（`MVVMWriter.cs`，第 42-89 行）检测 CommunityToolkit.Mvvm（`[ObservableObject]`）、Prism（`SetProperty(ref T, T, string)`）、ReactiveUI（`IReactiveObject`）与 Caliburn.Micro（`NotifyOfPropertyChange(string)`），并让生成的 setter 委托给该框架的通知方法，而不是自行触发事件。
