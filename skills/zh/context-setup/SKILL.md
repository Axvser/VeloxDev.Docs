# 上下文确认

## 职责

确认所有必要的上下文

## 流程

1.基于MainSKILL_Path，推导CloudGlyph_Child_Git的值

2.Project_Root必须由用户提供

3.LanguageTargets_List必须由用户提供，且必须是LanguageMap_List的子集，若不是子集，告知用户需要编辑LanguageMap_List以支持用户指定的语言

4.识别项目涉及的技术栈（编程语言、框架、构建工具、包管理器等），不预设任何特定技术

5.可选接受用户提供的SKILL路径，若提供则加载对应SKILL

6.**检查Wiki_Root现有内容** — 扫描Wiki_Root下各语言目录的现有文件结构，记录已存在的页面树，明确哪些维度已有内容、哪些为空，此信息将传递到后续编写阶段以避免重复或覆盖

7.汇总表给到用户，待其确认后可继续工作流
