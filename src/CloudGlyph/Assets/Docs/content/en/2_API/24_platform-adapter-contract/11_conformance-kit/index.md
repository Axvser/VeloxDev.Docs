# Conformance kit

`VeloxDev.AdapterTestKit` is a non-packable project under `Src/Test/Headless/`. It supplies the one graph every headless adapter suite drives, so a failure reports the adapter rather than the test's own fixture.

## Namespace

`VeloxDev.AdapterTestKit`, project `Src/Test/Headless/VeloxDev.AdapterTestKit/VeloxDev.AdapterTestKit.csproj`. The project sets `<IsPackable>false</IsPackable>`; reference it as a project.

## TestGraph

**Signature:** `sealed class TestGraph`

| Member | Type | Description |
| --- | --- | --- |
| `Tree` | `TreeDefaultViewModel` | The tree the adapter renders; its helper is `TreeHelper(200d)`. |
| `Left` | `NodeDefaultViewModel` | Left node at `(40, 40)`; its output slot is the sender. |
| `Right` | `NodeDefaultViewModel` | Right node at `(320, 40)`; its input slot is the receiver. |
| `LeftOutput` | `SlotDefaultViewModel` | Sender port, anchored at `(200, 85, 0)`. |
| `RightInput` | `SlotDefaultViewModel` | Receiver port, anchored at `(320, 85, 0)`. |
| `Link` | `ILinkComponent?` | The single link, or `null` when built unconnected. |
| `Far` | `NodeDefaultViewModel` | A node at `(6000, 4000)` that only a scrolled viewport can see. |
| `Create(bool connect = true)` | `static TestGraph` | Builds the deterministic graph. |

`Create` uses the component helpers directly, not the generated commands, because the helpers are synchronous. The tree deliberately uses the cell-size `TreeHelper(200d)` constructor: the default `TreeHelper()` has virtualization off, while a surface writes `Viewport` unconditionally.

```csharp
var graph = TestGraph.Create();          // left → right link
var tree = graph.Tree;
var far = graph.Far;                     // outside the default viewport

Console.WriteLine(tree.GetHelper().VisibleItems.Count);
```

**Expected result:** `graph.Link` is non-null after a connected create; `graph.Far` is absent from `tree.GetHelper().VisibleItems` at the origin.

## Headless coverage

The suites live under `Src/Test/Headless/` for WPF, Avalonia, WinForms, Razor and Jalium. WinUI and MAUI have demos but **no windowless host**, so they have no headless suite; `Src/Test/Headless/README.md` records this. A WinUI or MAUI page in this tree therefore documents a demo-verified surface, not a headless-verified one.
