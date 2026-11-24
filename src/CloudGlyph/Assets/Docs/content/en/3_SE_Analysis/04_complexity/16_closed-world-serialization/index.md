# Closed-world serialization

Serialization is a graph walk with a reference table: every distinct object is written once, a repeat becomes a reference id, and the reader registers each instance before reading its members so cycles resolve. The registry is a lock-free snapshot of dictionaries, so type dispatch is constant-time. The non-obvious cost is on the read side: the generated reader is a linear `if / else if` chain over member names, which makes member dispatch quadratic in the number of members per type.

Notation: $V$ distinct objects, $E$ member/edge references, $k_v$ members on the type of object $v$, $L$ average member-name length, $D$ document size, $W$ registered types, $B$ reader buffer.

## Cost model

| Operation | Time | Space | Source |
|---|---|---|---|
| `Serialize` | $O(V + E)$ | writer $O(V)$ refs + output $O(D)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:56` |
| `WriteValue` per object | $O(1)$ registry lookup + $O(k)$ member writes | — | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:136` |
| Repeat-object reference | $O(1)$ identity-hash probe | $O(1)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonWriter.cs:122` |
| `Deserialize` | $O(V + E + \sum_v k_v^2)$ | reader $O(V)$ refs + document | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:257` |
| Generated member dispatch | $O(k^2 L)$ per object | — | `Src/Generators/VeloxDev.Core.Generator/Writers/VeloxJsonCodeWriter.cs:272` |
| Registry lookup | $O(1)$ avg, lock-free | snapshot $O(W)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonRegistry.cs:268` |
| Register one type | $O(W)$ copy-on-write | $O(W)$ | `Src/Core/VeloxDev.Core/Serialization/VeloxJsonRegistry.cs:196` |

## Writing stops at a repeated reference

The writer keeps identity references in a dictionary; a second occurrence emits a reference id instead of descending again:

```csharp
if (_references.TryGetValue(instance, out var existing))
{
    WriteReference(existing);
    return false;
}

_references[instance] = _nextReferenceId++;
```

Source: `Src/Core/VeloxDev.Core/Serialization/VeloxJsonWriter.cs:126-132`

That is what makes a cyclic graph terminate. Each object costs one registry dispatch plus one write per member, so the total is $O(V + E)$; the reference table is $O(V)$.

## Reading is dispatched by a linear name chain

The generated reader loops members and compares each name against constants in order:

```csharp
while (reader.NextMember())
{
    if (reader.MemberNameEquals("A")) { ... }
    else if (reader.MemberNameEquals("B")) { ... }
    ...
    else reader.SkipValue();
}
```

Source: `Src/Generators/VeloxDev.Core.Generator/Writers/VeloxJsonCodeWriter.cs:272-296` (shape)

`MemberNameEquals` compares in place without allocating a string, but the separation is $O(L)$ per comparison. The $j$-th member is compared after $j-1$ failed comparisons, so one object costs $O(k^2 L)$ name comparisons in the worst case. The reader itself is otherwise linear:

```csharp
if (!reader.BeginObject(out var referenceId, out var typeName))
    return reader.ResolveReference(referenceId);
...
var registered = VeloxJsonRegistry.ReaderFor(actualType);
...
reader.RegisterReference(referenceId, instance);
registered.Read(reader, instance);
```

Source: `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs:456-480`

$$
T_{\text{deserialize}} = O\!\left(V + E + \sum_{v} k_v^2 L\right)
$$

For the view-model graphs this library targets, member counts are small (single digits), so the quadratic term is a small constant in practice. It becomes visible only for types with tens of members.

```plot
{
  "title": "Member dispatch: name chain vs hash",
  "grid": true,
  "xAxis": { "domain": [0, 60] },
  "yAxis": { "domain": [0, 3600] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(k), hash dispatch" },
    { "fn": "x*x", "color": "#f472b6", "title": "O(k^2), linear if/else chain" }
  ]
}
```

## The registry is a snapshot

Five dictionaries — writers, readers, container factories, names, and reverse names — are published together through a volatile snapshot. Lookups are one `TryGetValue` with no lock. Registration is copy-on-write: replacing a table copies it, so one registration costs $O(W)$ and the initial registration of all types costs $O(W^2)$ over the process lifetime. Module-initializer registration happens once per assembly at load, not per document.

## Closed world

There is no reflection fallback. A value whose type has no generated writer throws; a member whose type has no generated reader throws, unless the declared type is `object`, in which case the value is read by document shape. That is what keeps the library trim- and AOT-safe: the type closure is fixed at compile time.

## Memory

The writer holds one reference dictionary and, on the async path, an 8 KB character buffer flushed at 4 KB. `Serialize()` returns a string, so the document exists twice transiently (writer plus `ToString` copy). The reader holds either the whole document string, $O(D)$, or a window buffer that grows to the largest single token, $O(B + \text{token})$; a nesting counter array grows to $O(\text{depth})$. The reference table is $O(V)$ on both sides.
