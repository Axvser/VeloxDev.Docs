# Attributes and Generated Members

The two generator triggers and the members they emit. All runtime types here are in `VeloxDev.MVVM`; the generated members are added to your own partial class.

## VeloxDev.MVVM

### Class: VeloxPropertyAttribute

Marks a field or a `partial` property as one the generator turns into a notifying property.

**Signature:**
`public class VeloxPropertyAttribute : Attribute`

**Attribute usage:** `AttributeTargets.Field | AttributeTargets.Property`, `AllowMultiple = false`, `Inherited = false`.

**Generated members for `[VeloxProperty] private int _priority;`**

| Member | Kind | Notes |
|---|---|---|
| `Priority` | property | Name derived from `_priority`; getter and setter |
| `OnPriorityChanging(int oldValue, int newValue)` | `partial void` | Called before assignment |
| `OnPriorityChanged(int oldValue, int newValue)` | `partial void` | Called after assignment |

The setter compares old and new, raises `PropertyChanging` / `PropertyChanged` when the declaring type does not already implement them, and calls both partial hooks with the two values. A field initializer still supplies the default value.

For a collection property the getter calls `ObservableCollectionTracker.EnsureSubscribed`, so a collection assigned directly to the backing field is still observed.

### Class: VeloxCommandAttribute

Marks a method as the body of a generated command.

**Signature:**
`public sealed class VeloxCommandAttribute(string name = "Auto", bool canValidate = false, int semaphore = 1) : Attribute`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | `"Auto"` | Command name. `"Auto"` derives it from the method name. |
| `canValidate` | `bool` | `false` | Requires a generated-validator partial implementation. |
| `semaphore` | `int` | `1` | Maximum concurrent executions. Values below 1 are clamped to 1. |

| Property | Type | Description |
|---|---|---|
| `Name` | `string` | The command's name. |
| `CanValidate` | `bool` | Whether executability is validated by a partial method. |
| `Semaphore` | `int` | The maximum number of concurrent executions. |

**Attribute usage:** `AttributeTargets.Method`, `AllowMultiple = false`, `Inherited = false`.

**Accepted body shapes.** No parameter, one parameter of any type, or 2–15 parameters; an optional trailing `CancellationToken` in every case. Return `void`, `Task`, `Task<T>`, `ValueTask` or `ValueTask<T>`. One combination is rejected: a `void` method that takes a `CancellationToken`.

**Generated members**

| Situation | Generated member |
|---|---|
| Ordinary method | `public IVeloxCommand {Name}Command { get; }` |
| Typed parameters with no method type parameters | `public IVeloxCommand<TParam, TResult> {Name}Command { get; }` (one parameter) or the matching arity |
| A parameter type uses the method's own type parameter | `public IVeloxCommand<TParam, TResult> Get{Name}Command<T>()` |
| `canValidate: true` | `private partial bool CanExecute{Name}Command(...)` |

The command object is built lazily on first read. The validator's parameters mirror the marked method's leading parameters; a method with none receives one `object? parameter`.

### Class: ObservableCollectionTracker

Subscribes generated collection handlers idempotently, keyed weakly by the collection instance.

**Signature:**
`public static class ObservableCollectionTracker`

| Member | Signature | Description |
|---|---|---|
| `EnsureSubscribed` | `void EnsureSubscribed(object? collection, NotifyCollectionChangedEventHandler handler)` | Subscribes `handler` once per collection; later calls are an O(1) lookup. Does nothing when `collection` is not `INotifyCollectionChanged`. |
| `Unsubscribe` | `void Unsubscribe(object? collection, NotifyCollectionChangedEventHandler handler)` | Detaches `handler` when a collection is replaced. The tracking entry survives, so a later `EnsureSubscribed` subscribes again. |

Handlers are compared by `(Method, Target)` identity rather than delegate reference, so a method group passed from the generated getter does not accumulate subscriptions.

## Generated collection hooks

For a property `Tags` of type `ObservableCollection<T>`, the generator declares four partial hooks and one generic infrastructure hook.

| Member | Signature | When it runs |
|---|---|---|
| `OnItemAddedTo{Name}` | `partial void OnItemAddedToTags(IEnumerable<T> items)` | `Add` and `Replace` add items |
| `OnItemRemovedFrom{Name}` | `partial void OnItemRemovedFromTags(IEnumerable<T> items)` | `Remove` and `Replace` remove items |
| `OnItemMovedIn{Name}` | `partial void OnItemMovedInTags(IEnumerable<T> items)` | `Move` |
| `OnItemsResetIn{Name}` | `partial void OnItemsResetInTags()` | `Clear` / reset |
| `OnCollectionChanged<T>` | `protected virtual void OnCollectionChanged<T>(string propertyName, NotifyCollectionChangedEventArgs e, IEnumerable<T>? oldItems, IEnumerable<T>? newItems)` | Every action, with old and new items; override for a single dispatch point |

If a base class already declares collection infrastructure, the generator reuses it rather than declaring a second one.

## Example

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "Untitled";
    [VeloxProperty] private int _priority = 1;
    [VeloxProperty] private ObservableCollection<string> _tags = new();

    partial void OnPriorityChanged(int oldValue, int newValue)
        => Console.WriteLine($"priority {oldValue} -> {newValue}");

    partial void OnItemAddedToTags(IEnumerable<string> tags)
        => Console.WriteLine($"added {string.Join(", ", tags)}");

    [VeloxCommand(canValidate: true)]
    private void Promote() => Priority++;

    private partial bool CanExecutePromoteCommand(object? parameter) => Priority < 3;
}
```

After a build, `Title`, `Priority`, `Tags` and `PromoteCommand` exist as ordinary members. See the [quick start](../../../1_QuickStart/11_mvvm-viewmodel-generation/index.md) for the runnable program.
