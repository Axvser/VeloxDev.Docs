# MVVM — `VeloxPropertyAttribute`

Marks a field or a `partial` property for the MVVM generator.

**Signature** (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`, lines 25-29):

```csharp
[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property, AllowMultiple = false, Inherited = false)]
public class VeloxPropertyAttribute : Attribute
{
}
```

- **Targets:** `Field` or `Property`. `AllowMultiple = false`, `Inherited = false`. Not sealed.
- **Notes:** A private field (`_index`) is expanded into a public property named after the field (underscore stripped, first letter upper-cased — `Base/Analizer.cs`, `GetPropertyNameFromFieldName`, lines 70-80). A `partial` property is completed with a generated backing field. When the type implements `INotifyCollectionChanged`, collection-tracking members are added (see `ObservableCollectionTracker`).
- **Example:** `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs`, lines 28-34 — `[VeloxProperty] private int _index = 0;` becomes a public `Index` property.
