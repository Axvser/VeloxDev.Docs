# MVVM 视图模型生成

`VeloxDev.MVVM` 命名空间与 `VeloxDev.Core.Generator` 分析器。两个特性驱动生成器：`[VeloxProperty]` 把字段或分部属性变成通知属性，`[VeloxCommand]` 把方法变成 `IVeloxCommand`。支撑一条生成命令的运行时类型——有界、排队、可取消的管线——也在同一命名空间，可绕过生成器直接使用。

生成器在编译期运行。引用 `VeloxDev.Core` NuGet 包会带上它；用 `ProjectReference` 时需单独添加为分析器引用。

## 类型分组

| 分组 | 类型 | 页面 |
|---|---|---|
| 特性与生成成员 | `VeloxPropertyAttribute`、`VeloxCommandAttribute`、生成的属性、命令与集合钩子、`ObservableCollectionTracker` | [特性与生成成员](00_特性与生成成员/index.md) |
| 命令运行时 | `CommandPipeline<TParam, TResult>`、`VeloxCommand`、`VeloxCommand<TParam, TResult>`、2–15 参数命令族、`CommandOutcome`、`CommandCompletion`、`CommandEventArgs`、`CommandEventType` | [命令运行时](01_命令运行时/index.md) |
| 命令接口与扩展 | `IVeloxCommand`、`IVeloxCommand<TParam, TResult>`、`IVeloxCommandStatus`、`IVeloxCommandResult`、`IVeloxCommandCompletion`、`IVeloxCommandEvents<TParam, TResult>`、`VeloxCommandExtensions` | [命令接口](02_命令接口/index.md) |

## 配置

无需注册。把类标为 `partial`、加上特性并构建；设置 `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` 后，生成的成员以普通 C# 出现在 `obj/` 下的 `*_MVVM.g.cs` 与 `*_Commands.g.cs` 文件中。完整程序见 [MVVM 视图模型生成快速开始](../../1_快速开始/11_MVVM视图模型生成/index.md)。

## 生成规则一览

- 字段 `_name` 生成属性 `Name`：去掉前导下划线并把首字母大写。
- 方法的命令名删除所有 `Async` 再追加 `Command`：`SaveAsync` 变成 `SaveCommand`。
- `[VeloxProperty]` 接受字段或 `partial` 属性；生成的 setter 触发 `INotifyPropertyChanging` 与 `INotifyPropertyChanged`。
- `[VeloxCommand(canValidate: true)]` 要求实现 `private partial bool CanExecute{Name}Command(...)`；不实现是编译错误。
- `ObservableCollection<T>` 属性获得惰性订阅与四个分部集合钩子。
