# MVVM — `VeloxPropertyAttribute`

标记一个字段或 `partial` 属性供 MVVM 生成器处理。

**签名**（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`，第 25-29 行）：

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **目标：** `Field` 或 `Property`。`AllowMultiple = false`、`Inherited = false`。未密封。
- **备注：** 私有字段（`_index`）会展开为公开属性，命名规则为去掉下划线并把首字母大写（`Base/Analizer.cs`，`GetPropertyNameFromFieldName`，第 70-80 行）。`partial` 属性会用生成的支撑字段补全。当类型实现 `INotifyCollectionChanged` 时，还会附加集合追踪成员（见 `ObservableCollectionTracker`）。
- **示例：** `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`，第 28-34 行 — `[VeloxProperty] private int _index = 0;` 变成公开的 `Index` 属性。
