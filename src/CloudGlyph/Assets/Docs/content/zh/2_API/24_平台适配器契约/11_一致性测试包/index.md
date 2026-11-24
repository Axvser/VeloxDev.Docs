# 一致性测试包

`VeloxDev.AdapterTestKit` 是 `Src/Test/Headless/` 下的不可打包项目。它提供每个无头适配器套件驱动的同一张图，使失败报告适配器而不是测试自己的夹具。

## 命名空间

`VeloxDev.AdapterTestKit`，项目 `Src/Test/Headless/VeloxDev.AdapterTestKit/VeloxDev.AdapterTestKit.csproj`。项目设置 `<IsPackable>false</IsPackable>`，因此以项目引用方式使用。

## TestGraph

**签名：** `sealed class TestGraph`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Tree` | `TreeDefaultViewModel` | 适配器渲染的树；其 Helper 为 `TreeHelper(200d)`。 |
| `Left` | `NodeDefaultViewModel` | 位于 `(40, 40)` 的左侧节点；其输出插槽是发送端。 |
| `Right` | `NodeDefaultViewModel` | 位于 `(320, 40)` 的右侧节点；其输入插槽是接收端。 |
| `LeftOutput` | `SlotDefaultViewModel` | 发送端口，锚点为 `(200, 85, 0)`。 |
| `RightInput` | `SlotDefaultViewModel` | 接收端口，锚点为 `(320, 85, 0)`。 |
| `Link` | `ILinkComponent?` | 唯一连线；以未连接方式构建时为 `null`。 |
| `Far` | `NodeDefaultViewModel` | 位于 `(6000, 4000)`、只有滚动视口才能看到的节点。 |
| `Create(bool connect = true)` | `static TestGraph` | 构建确定性图。 |

`Create` 直接使用组件 Helper 而非生成的命令，因为 Helper 是同步的。树刻意使用单元格尺寸构造函数 `TreeHelper(200d)`：默认 `TreeHelper()` 关闭虚拟化，而表面会无条件写入 `Viewport`。

```csharp
var graph = TestGraph.Create();          // 左 → 右连线
var tree = graph.Tree;
var far = graph.Far;                     // 默认视口之外

Console.WriteLine(tree.GetHelper().VisibleItems.Count);
```

**预期结果：** 连接式创建后 `graph.Link` 非空；在原点时 `graph.Far` 不在 `tree.GetHelper().VisibleItems` 中。

## 无头覆盖

套件位于 `Src/Test/Headless/`，覆盖 WPF、Avalonia、WinForms、Razor 与 Jalium。WinUI 与 MAUI 有 demo，但**没有无窗口宿主**，因此没有无头套件；`Src/Test/Headless/README.md` 记录了这一点。因此本树中的 WinUI 或 MAUI 页面描述的是 demo 验证过的表面，而不是无头验证过的表面。
