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
> 使用本模板即可获得你自己的 Agent 驱动 Wiki 站点。

---

## 🚀 人类快速上手

1. **创建你的 Wiki 仓库** — 从本模板在 GitHub 上创建
2. **克隆**到本地
3. **告诉你的 Agent** 阅读本 README
4. **推送** — GitHub Action 自动部署到 Pages

---

## 🤖 给 AI 编码 Agent

> 如果你是一个正在阅读本文的 AI 编码 Agent，请协助你的主人完成下述步骤：
> **获取或更新 Cloud Glyph 自身**，以便使用其技能系统。
>
> 1. **假定你的主人已经完成从Cloud Glyph模板仓库创建独立仓库并克隆到本地**
>	1.1 执行 `python sync_template.py <your-wiki-path>` 来同步文件
>	1.2 若你是Claude，可运行 `python <仓库根目录>/skills/claude_install.py <claude-dir>`，这将在 .claude/ 所在目录下，执行skills安装操作
>	1.3 非Claude用：`python <仓库根目录>/skills/gen_skill.py --lang <en|zh>`直接获取SKILL.md，并按你自己的规范去处置这个文件
> 2. **如果你是基于任何工具、MCP服务远程访问到这个文件而无本地仓库**
>	2.1 告诉用户从本模板创建自己的仓库并克隆到本地
>   2.2 确认用户操作完成后再返回到第一种情况并执行

---

## 📤 发布

### 配置 GitHub Pages

在你的 Wiki 仓库的 GitHub **Settings → Pages** 中，将 **Build and deployment → Source** 设置为 **`GitHub Actions`**。

### 推送

```bash
cd <your-wiki-path>
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
python sync_template.py <your-wiki-path>
```

该脚本会从 GitHub 拉取最新模板，同步所有文件（skills、配置、工作流等），并保留 `src/CloudGlyph/Assets/Docs/content/` 下你已有的内容。

同步后，为每种语言重新生成 SKILL：

```bash
python skills/gen_skill.py --lang en
python skills/gen_skill.py --lang zh
```

如果使用 Claude，重新安装：

```bash
python skills/claude_install.py <claude-working-dir> --lang en
```