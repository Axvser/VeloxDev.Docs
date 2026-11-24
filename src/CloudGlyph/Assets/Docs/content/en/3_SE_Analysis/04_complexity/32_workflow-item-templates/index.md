# Workflow Item Templates

A template pack is a `dotnet new` item: seven roles per platform, seven platforms, 49 items in all. Generation is a linear file-materialisation pass with token replacement — there is no conditional content, no chained template and no post-action. The only runtime complexity a template owns is the selector's type switch.

## Cost model

| Symbol | Meaning |
|---|---|
| $P$ | packs (7 platforms) |
| $R$ | roles per pack (7) |
| $F$ | files emitted by one role (1 or 2) |
| $f_i$ | files in item $i$ |
| bytes | emitted file size |

## Item inventory

Each pack directory contains exactly seven role folders, each with one `.template.config/template.json`, for 49 manifests in total (`Src/Templates/*/working/content/*/.template.config/template.json`). A WPF node item declares its identity and one source name (`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-node-view/.template.config/template.json`).

```json
"identity": "VeloxDev.WPF.WorkflowNodeView",
"name": "VeloxDev WPF Workflow Node View",
"shortName": "wpf-v-node",
"sourceName": "TemplateClass",
"defaultName": "NodeView",
"preferNameDirectory": false,
"tags": {
  "language": "C#",
  "type": "item"
},
```

The roles are tree, node, slot, link, selector, decorator and minimap; short names are `{prefix}-v-{role}`. A view role emits a markup file and a code-behind; a pure code role emits one `.cs`, except Razor's selector, decorator and minimap which also carry a `.razor.cs`.

## Generation cost

Generation is proportional to the number of files materialised, and each file costs one read, one token replacement per declared symbol, and one write.

$$
T_{\text{new}} = O\left(\sum_{i=1}^{P \cdot R} f_i \cdot (1 + s_i)\right) = O(P \cdot R \cdot F)
$$

All 49 packs together emit 80 files: 11 per platform for six platforms and 14 for Razor. There is no globbing, no generator symbol and no dependency between packs; the work is independent per item and parallel-safe at the process level.

Space is the sum of emitted file sizes, $O(\text{bytes})$, since `dotnet new` renders each file into memory before writing.

## Symbol substitution

Each pack declares a handful of text parameters — namespace, colours, thicknesses — with `replaces` strings that mark the placeholders. Substitution is a linear replace per symbol per file. The WinForms pack carries one extra parameter because its surface background appears in an additional template, but the asymptotic shape is unchanged.

There is no `condition`, `choice` or `value` symbol in any of the 49 manifests: per-platform differences are baked into file contents rather than selected at generation time. That keeps generation linear and makes the emitted output deterministic for a given platform and name.

## Runtime cost of a generated selector

The selector template emits a `DataTemplateSelector` with a fixed four-arm type switch (`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-template-selector/TemplateClass.cs:18-31`).

```csharp
public override DataTemplate SelectTemplate(object item, DependencyObject container)
    => item switch
    {
        ILinkComponent => LinkTemplate
            ?? throw new InvalidOperationException("LinkTemplate is not set."),
        ISlotComponent => SlotTemplate
            ?? throw new InvalidOperationException("SlotTemplate is not set."),
        INodeComponent => NodeTemplate
            ?? throw new InvalidOperationException("NodeTemplate is not set."),
        _ => throw new InvalidOperationException($"Unsupported workflow item: {item?.GetType().FullName}")
    };
```

Selection is $O(1)$ per item and allocation-free on the hit path. A drawn frame that realises $v$ items therefore costs $O(v)$ selector calls, indistinguishable from the pool's own $O(v)$ materialisation.

## What a pack does not do

A pack contains no view hosting, no pool policy and no drawing loop; those come from the adapter. The generated views participate in the costs analysed under each adapter — 128-sample curves, damage rectangles, retained minimap elements — and the template only fixes their source shape. This is why the template's own complexity is dominated by file count rather than by graph size.

## Related

- [Platform Adapter Contract](../24_platform-adapter-contract/index.md) — the role set the templates implement.
- [WPF Adapter](../25_wpf-adapter/index.md) — one concrete cost profile of the generated views.
