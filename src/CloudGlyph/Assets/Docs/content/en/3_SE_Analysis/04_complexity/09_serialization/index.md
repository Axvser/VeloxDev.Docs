# Complexity Analysis — Serialization

The archive engine has no reflection and no contract cache, so its cost model is unusually simple: a lookup that is a dictionary read, and a traversal that visits each object once. Constants below assume $P$ = the number of members actually written.

## The traversal

Writing walks the object graph through generated code. Every object is visited once — the writer gives it an id and writes its members; a second sighting writes a reference instead (`VeloxJsonWriter.cs:122-142`). Traversal is therefore linear in the number of written members, not in the size of the reachable object graph.

$$
T_{\text{serialize}} = O(P), \qquad T_{\text{deserialize}} = O(P)
$$

where $P$ is bounded by $O(V + E + \text{member count})$ for a workflow tree of $V$ nodes and $E$ links — and, crucially, is *bounded by the compiled member set* rather than by what a runtime walk happens to find. A read-only member such as a node's `Helper` is not a candidate at all (`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:912-1025`), so it can never contribute to $P$.

Both directions are a single pass: the reader is a forward-only cursor over one document (`NextMember` advances, `MemberNameEquals` compares in place), so a member that appears late in the document is not re-visited for a member that appears early.

## The lookup

$$
T_{\text{resolve}} = O(1)
$$

`WriterFor(type)` / `ReaderFor(type)` are dictionary reads against an immutable snapshot held behind a `volatile` field (`VeloxJsonRegistry.cs:83-96`). There is no lock on the read path and no cache to warm: the snapshot a reader sees is a complete, self-consistent table, because every registration publishes a **new** snapshot rather than mutating the old one.

That is the whole reason the hot path is branch-light — and it is also why registry writes are deliberately boring: they happen once per assembly load and are never on a measured path.

## Per-member allocation

Member names are compared **in place** rather than interned, so neither the writer nor the reader allocates a string per member. That leaves per-member cost at:

$$
T_{\text{member}} = O(1) + O(\text{escaping})
$$

where the escaping term is itself linear in the *string's length*, not in the document's. String escaping and `double` spelling have exactly one implementation — `VeloxJsonText` — shared by the archive writer and the in-memory JSON tree, so there is no second copy to drift (`Serialization/VeloxJsonText.cs:13`).

## Document size

$$
S_{\text{json}} = O(P \cdot \text{avg bytes per value})
$$

The measured advantage over `System.Text.Json` and Newtonsoft is **not** asymptotic — all three are linear in what they write. It is a constant factor that comes from writing *less*: fewer members are in the closed world than reflection would find, references are written once rather than expanded, and member names are not repeated on every node. The repository's own benchmark notes are explicit that the three writers do not write the same member set, so a raw time ratio between them is not a like-for-like comparison.

## Summary

| Operation | Time | Space | Basis |
|---|---|---|---|
| `WriterFor` / `ReaderFor` | $O(1)$ | $O(1)$ | dictionary read against an immutable snapshot; no lock |
| `Serialize` (write) | $O(P)$ | $O(P)$ output | one visit per object; repeats become references |
| `Deserialize` (read) | $O(P)$ | $O(P)$ | forward-only cursor, member order irrelevant |
| Per-member | $O(1)$ | $O(1)$ as a rule | names compared in place, never interned |
| Registry registration | $O(1)$ amortized | $O(\text{new snapshot})$ | once per assembly load, off the measured path |
| `CompiledGraphEx` snapshot | $O(P_{\text{graph}})$ | $O(P_{\text{graph}})$ | the writer stops at the graph boundary by declared-type exclusion |
