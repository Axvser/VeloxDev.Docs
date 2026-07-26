<h1 align="center">Cloud Glyph</h1>

<p align="center">
  基于 <a href="https://www.avaloniaui.net/">Avalonia UI</a> 框架构建的浏览器端 Wiki 站点生成器
</p>

<p align="center">
  <strong>Agent 编写 → 一键部署到 GitHub Pages</strong>
  <br />
  AI Agent 按 <code>skills/</code> 指令编写 Wiki → CloudGlyph 构建 → 自动发布到 Pages
</p>

<p align="center">
  <a href="README.md">🇬🇧 English</a>
</p>

---

> **🌐 线上站点：** [https://axvser.github.io/CloudGlyph/](https://axvser.github.io/CloudGlyph/)
>
> 使用本模板并按照本指南操作，即可获得你自己的 Agent 驱动 Wiki 站点。

---

## 🤖 Agent 说明

> **如果你是一个正在阅读本 README 的 AI 编码 Agent：** 你的任务是使用本技能系统构建 Wiki 文档。
>
> 读取 **`skills/SKILL.md`** 并按照管线执行。

---

## 🚀 两种使用模式

本模板支持两种部署模式。Agent 会自动检测当前模式。

| 模式 | 场景 | Agent 行为 |
|---|---|---|
| **嵌套** | Wiki 仓库作为子目录克隆到项目内部 | 自动发现项目并为其写文档（排除自身） |
| **独立** | Wiki 仓库独立使用（周围没有项目） | 询问用户要文档化的项目路径 |

---

## 📁 模式一：嵌套（Wiki 放在项目内）

将 Wiki 仓库作为子目录克隆到你的项目中。Agent 可在同一工作区中同时访问源代码和 Wiki 指令。

### 设置

```bash
# 在你的项目仓库中，创建一个用于 Wiki 的分支
git checkout -b docs/wiki-content

# 将你的 Wiki 仓库克隆为子目录
git clone https://github.com/<你的用户名>/MyProject-Wiki.git docs/wiki
```

项目结构如下：

```
your-main-project/                     ← 你的实际代码（Agent 文档化此部分）
├── src/
├── tests/
├── docs/wiki/                         ← 你的 Wiki 仓库（Agent 排除此目录）
│   ├── skills/
│   │   ├── SKILL.md                   ← 入口点
│   │   └── ...
│   └── src/CloudGlyph/Assets/Docs/content/
└── README.md
```

> **⚠️ .gitignore 风险：** 如果你项目的 `.gitignore` 包含 `src/` 或 `**/Docs/**` 等模式，Wiki 输出文件可能被忽略。添加 `!docs/wiki/**` 来豁免 Wiki 目录。

### 指挥 Agent

> "读取 `docs/wiki/skills/SKILL.md` 并按照管线执行。"

---

## 🏠 模式二：独立（Wiki 作为独立仓库）

单独使用 Wiki 仓库——例如为不想修改源代码的项目编写文档。

### 设置

将本仓库直接在工作区中打开（无需嵌套项目）。如果愿意，可以将目标项目源码一同放在工作区中。

### 指挥 Agent

> "读取 `skills/SKILL.md` 并按照管线执行。"

Agent 会检测到**独立**模式，并询问你要文档化的项目路径。

---

## 📤 发布

### 1. 配置 GitHub Pages

在你的 Wiki 仓库的 GitHub **Settings → Pages** 中，将 **Build and deployment → Source** 设置为 **`GitHub Actions`**。

### 2. 推送

```bash
cd docs/wiki       # 或你的 wiki 路径
git add .
git commit -m "添加 Wiki 内容"
git push origin master
```

你的发布站点地址为：

```
https://<你的用户名>.github.io/MyProject-Wiki/
```

> **自动部署：** GitHub Actions 工作流在检测到 `src/CloudGlyph/Assets/Docs/**` 下的推送时自动触发。

---

## 🔄 保持技能更新

CloudGlyph 的 `skills/` 目录可能会收到更新。要将你的 Wiki 仓库与最新的上游模板同步，同时保留已编写的文档：

```bash
cd <your-wiki-path>
python sync_template.py
```

该脚本会从 GitHub 拉取最新模板，同步所有文件（skills、配置、工作流等），并保留 `src/CloudGlyph/Assets/Docs/content/` 下你已有的内容。

> **注意：** `sync_template.py` 是**面向用户**的工具。同步后，为每种语言重新生成技能索引：
>
> ```bash
> python skills/gen_skill.py --lang en
> python skills/gen_skill.py --lang zh
> ```
>
> `gen_skill.py` 是内部开发工具。