# JSON Tree

An in-memory JSON value used to build tool results and configuration payloads and render them with the same spelling rules as the archive format. Namespace `VeloxDev.Serialization`.

## VeloxDev.Serialization

### Class: VeloxJsonValue

The abstract tree node. Scalars convert implicitly from the primitives.

**Signature:** `public abstract class VeloxJsonValue`

| Member | Signature | Description |
|---|---|---|
| `ToJson` | `string ToJson(VeloxJsonFormat format = VeloxJsonFormat.Compact)` | Renders the tree as text. |
| `ToString` | `override string ToString()` | `ToJson()`. |
| `IsNull` | `virtual bool IsNull { get; }` | Whether this value is the JSON `null`. |
| `Materialize` | `virtual object? Materialize()` | Turns the tree into CLR values: `string`, `bool`, `long` / `double`, `Dictionary<string, object?>`, `List<object?>`, or `null`. |
| `DeepEquals` | `virtual bool DeepEquals(VeloxJsonValue? other)` | Member-for-member and element-for-element equality; member order is not part of the answer. |
| `From` | `static VeloxJsonValue From(object? value)` | Builds a tree from a value. A type the archive serializer knows goes through its generated writer rather than a reflection walk. |
| `Parse` | `static VeloxJsonValue Parse(string json)` | Parses text into a tree; throws `FormatException` for invalid JSON. |
| `Null` | `static VeloxJsonValue Null { get; }` | The JSON `null` literal. |

**Implicit conversions:** `string?`, `bool`, `int`, `long` and `double` to `VeloxJsonValue`.

### Class: VeloxJsonScalar

A string, number, boolean or `null`, kept as the text that will be written.

**Signature:** `public sealed class VeloxJsonScalar : VeloxJsonValue`

| Member | Type/Signature | Description |
|---|---|---|
| `Text` | `string? { get; }` | The text as it will be written. |
| `AsString` | `string? AsString()` | The text. |
| `AsInt32` | `int AsInt32()` | The number, or `0` when it is not one. |
| `AsBoolean` | `bool AsBoolean()` | `text == "true"`. |
| `IsNumber` | `bool { get; }` | A bare numeric literal; a quoted numeric string stays text. |
| `IsText` | `bool { get; }` | Whether the scalar came from a quoted string. |
| `DeepEquals` / `Materialize` | overrides | Kind and text are both compared. |

### Class: VeloxJsonArray

An ordered array.

**Signature:** `public sealed class VeloxJsonArray : VeloxJsonValue, IEnumerable<VeloxJsonValue>`

| Member | Signature | Description |
|---|---|---|
| `Count` | `int { get; }` | Element count. |
| `this[int]` | `VeloxJsonValue this[int index] { get; }` | The element at a position. |
| `Add` | `void Add(VeloxJsonValue value)` | Appends an element; `null` becomes the JSON literal. |
| `Add` | `void Add(object? value)` | Appends an element built by `From`. |
| `Clear` | `void Clear()` | Removes every element. |
| `GetEnumerator` | `IEnumerator<VeloxJsonValue> GetEnumerator()` | Enumerates in order. |

### Class: VeloxJsonObject

An object whose members keep insertion order.

**Signature:** `public sealed class VeloxJsonObject : VeloxJsonValue, IEnumerable<KeyValuePair<string, VeloxJsonValue>>`

| Member | Signature | Description |
|---|---|---|
| `Count` | `int { get; }` | Member count. |
| `Names` | `IEnumerable<string> { get; }` | Member names, in order. |
| `this[string]` | `VeloxJsonValue? this[string name] { get; set; }` | Gets or sets a member. Setting an existing member replaces it in place; setting `null` removes it. |
| `Has` | `bool Has(string name)` | Whether the object has that member. |
| `Add` | `void Add(string name, VeloxJsonValue value)` | Adds or replaces a member. |
| `GetEnumerator` | `IEnumerator<KeyValuePair<string, VeloxJsonValue>> GetEnumerator()` | Enumerates members in order. |
| `ToDictionary` | `Dictionary<string, object?> ToDictionary()` | The materialized map. |

## Example

```csharp
using VeloxDev.Serialization;

var result = new VeloxJsonObject();
result["ok"] = true;
result["count"] = 3;
result["items"] = new VeloxJsonArray { "alpha", "beta" };

string compact = result.ToJson(VeloxJsonFormat.Compact);
string indented = result.ToJson(VeloxJsonFormat.Indented);

VeloxJsonValue parsed = VeloxJsonValue.Parse(compact);
Console.WriteLine(parsed.DeepEquals(result));          // True
var map = (Dictionary<string, object?>)parsed.Materialize()!;
```

## Notes

- A scalar read from a document comes back as text rather than a typed value; use `AsInt32` / `AsBoolean` to read it.
- `From` handles scalars, dictionaries (including `IReadOnlyDictionary<string, object?>`), enumerables, and any type the archive serializer has a writer for. Anything else throws `InvalidOperationException`.
- `DeepEquals` ignores member order and is what the state snapshots use to tell one payload from the next.
