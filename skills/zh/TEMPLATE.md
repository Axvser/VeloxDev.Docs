---
name: cloud-glyph-wiki-create
description: 分析工程源码，产出美观、规范的Wiki文档
---

## 职责

严格遵循该SKILL定义的工作流，产出符合规范的Wiki文档

## 变量约定

必须尊重下述变量约定，对于不确定的变量，先尝试自行推断，如果无法推断，直接询问用户，在工作流开始前，输出最终表格，直到用户确认无误才可开始工作流

> CloudGlyph_Git:[https://github.com/Axvser/CloudGlyph][ReadOnly][Template Repository] - Cloud Glyph 仓库地址

> CloudGlyph_Child_Git:[request] - 本地Wiki仓库根目录，该Wiki仓库是基于Cloud Glyph:[Template Repository]创建的独立仓库，自身不计入Wiki分析或编写

> Project_Root:[request] - 待文档化的项目的根目录

> MainSKILL_Path:[CloudGlyph_Child_Git/skills/SKILL.md] - 当前技能所在路径

> Wiki_Root:[CloudGlyph_Child_Git/src/CloudGlyph/Assets/Docs/content/{languages}/] - 产出文档的根目录，按language划分的动态变量，例如编写英语时，它就是CloudGlyph_Child_Git/src/CloudGlyph/Assets/Docs/content/en/，Agent仅允许在Wiki_Root下编辑文档内容

> LanguageMap_List:[CloudGlyph_Child_Git/src/CloudGlyph/Assets/Docs/config/languages.json] - Wiki支持语言的范围

> LanguageTargets_List:[request] - 用户希望Wiki支持的语言范围

## 分析范式

⚙ **Wiki 的内容以「功能」为基本单元进行划分，而不是以 Project 的目录结构进行划分**。目录结构是项目的一种实现细节，可能随架构演进、团队习惯而变化，不应直接映射为 Wiki 结构。

⚙ 功能（Feature）的定义：一个功能是项目对外提供的一组内聚能力，通常对应一个可独立描述、独立使用、独立验证的使用场景。同一功能可能横跨多个目录/工程，同一目录下也可能并存多个功能——判定以功能为准，目录仅作为查找线索。

⚙ 功能/API 的发现顺序与路径（按优先级从高到低）：

1. **入口理解** — 先阅读项目的 README、入口文件、构建脚本等，建立对项目整体意图的认知，形成候选功能列表
2. **Demo / Example 优先** — 扫描 Examples/、samples/、demo 等目录并完整阅读全部源文件，Demo 是功能与 API 的第一证据源
3. **测试驱动** — 某个功能若缺少 Demo，完整阅读对应测试文件，从用例中提取功能边界与典型用法
4. **源码兜底** — 仅当以上均缺失时才从源码目录结构与接口签名推断功能，此类推断必须明确标注为「推断所得」

⚙ 上述顺序适用于所有项目规模：单工程、多工程、大型框架/单体仓库一视同仁；大型项目尤其禁止仅凭目录名猜测功能。

⚙ 分析产物：一份「功能清单」，逐项列出 功能名 / 归属工程 / 对外 API 面 / 证据来源（Demo / Test / 推断）。该清单是后续【快速开始】【API】【SE分析】各阶段统一的工作输入，三个阶段围绕同一份功能清单展开，保证 Wiki 各维度口径一致。

⚙ Wiki 的五个固定维度（见【结构约定】）下的子项展开一律以功能为单位组织。

## 结构约定

⚙ {ID}_{PageName}/ - 产出Markdown时采取的文件夹命名规则，文件夹构成的树结构就是最终App渲染Wiki时看到的目录结构

⚙ index.md - 每个{ID}_{PageName}/下都必须有且仅有一个固定名称的index.md文件，否则将导致目录结构不完整，md文件可留白，可以加更多子目录表示子项

⚙ 输出路径下的**每一个**目录都必须包含 index.md——包括中间父目录，不仅限于叶子目录。创建新的子目录后，立即确认该路径的每一级祖先目录都有 index.md。常见错误是创建了例如 `2_设计模式/0_工作流/index.md` 但遗忘了 `2_设计模式/index.md`。

最终，目录会呈现下述结构，这是五个固定的维度

> Wiki_Root/0_欢迎/

> Wiki_Root/1_快速开始/.../

> Wiki_Root/2_API/.../

> Wiki_Root/3_SE分析/.../

> Wiki_Root/4_版权/.../

## 模板约定

⚙ 本 SKILL 配有可选模板，汇总于「模板索引」表，列为 `适用时机 (When) | 模板内容 (Template)` 的映射。

⚙ 使用时按「适用时机」匹配当前场景选择对应模板；模板内容以转义形式存储，需解析还原后使用。

## 编码风格约定

⚙ **代码缩进一律使用实际空格字符（Space），禁止使用制表符（Tab / \t）**。所谓缩进，是指确定数量的空格，例如 4 个空格；Tab 在不同渲染环境下的显示宽度不可控，不允许出现在 Wiki 代码块中。

⚙ 在编写 Wiki 代码块前，扫描【Project_Root】下的源文件检测项目的主导缩进宽度（2 空格、4 空格等），生成的代码块缩进必须与其匹配。检测有歧义时默认使用 **4 空格**。

⚙ 从源文件（Demo / Test / 源码）提取代码片段时，将源文件中的制表符统一转换为检测到的空格宽度（默认 4 空格），确保 Wiki 内所有代码块均为实际空格缩进。

## 可访问性约定

⚙ 尊重源代码中明确标记为非public的内容，避免在Wiki中暴露这些内容

⚙ 避免在Wiki中暴露敏感信息，如密码、密钥、个人信息等

## 工作流

<!-- WORKFLOW -->

