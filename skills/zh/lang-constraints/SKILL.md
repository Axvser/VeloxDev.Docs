# 约束加载

## 职责

在确定技术栈后，加载对应语言的文档编写约束。此技能本身是调度器，具体约束定义在嵌套子技能中。

## 调度逻辑

根据 tech-analysis 输出的技术栈检测结果，加载对应的语言约束子技能：

| 检测结果 | 加载子技能 |
|---|---|
| .NET (C# / VB / F#) | `lang-constraints/dotnet/SKILL.md` |
| Rust | `lang-constraints/rust/SKILL.md` |
| TypeScript / JavaScript | `lang-constraints/typescript/SKILL.md` |
| Python | `lang-constraints/python/SKILL.md` |
| Go | `lang-constraints/go/SKILL.md` |
| C / C++ | `lang-constraints/c-cpp/SKILL.md` |
| Java | `lang-constraints/java/SKILL.md` |
| 无法识别 | 使用通用文档规约（无需加载子技能） |

## 示例

```
# 假设 tech-analysis 检测到 .slnx 和 .csproj 文件
→ 加载 skills/lang-constraints/dotnet/SKILL.md
  该约束将指导 Agent 使用 XML doc comments、记录 DI 生命周期等
```

## 输出

将加载的约束规则合并到 Agent 的工作内存中，后续文档编写步骤自动遵守这些规则。
