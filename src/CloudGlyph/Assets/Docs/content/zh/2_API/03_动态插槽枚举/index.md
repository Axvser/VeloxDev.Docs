# 动态插槽枚举

`SlotEnumerator<TSlot>` 把一个选择器值映射到一个插槽。选择器可以是枚举、`bool` 或 `ISlotProvider` 实例；切换它以一步可撤销操作重建整套端口。

- [插槽枚举器](00_插槽枚举器/index.md) — `SlotEnumerator<TSlot>`、它的选择状态与重建规则。
- [条件插槽与提供者](01_条件插槽与提供者/index.md) — `ConditionalSlot<TSlot>`、`SlotDefinition`、`ISlotProvider`、提供者接口与 `[SlotSelectors]`。

```csharp
var node = new NodeDefaultViewModel();
var ports = new SlotEnumerator<SlotDefaultViewModel>();
ports.Install(node, nameof(ports));
ports.SetSelector(typeof(DayOfWeek));

Console.WriteLine(ports.Count);      // 7
Console.WriteLine(ports.TrySelect(DayOfWeek.Monday, out var slot));
```

任务式教程见[动态插槽枚举](../../1_快速开始/03_动态插槽枚举/index.md)。
