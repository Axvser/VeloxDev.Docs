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

1. **创建你的 Wiki 仓库** — 在 GitHub 上从本模板创建（“Use this template”）
2. 在需要由 CloudGlyph 生成 Wiki 的宿主仓库中（约定：仓库根目录）把该 Wiki 仓库作为 git 子模块加入：

   ```bash
   git submodule add <your-wiki-repo-url> Wiki
   ```

3. **告诉你的 Agent** 阅读本 README
4. **在 `Wiki/` 内推送** — 该仓库自己的 GitHub Action 会自动部署到 Pages — 再在宿主仓库提交更新后的子模块指针

---

## 🤖 给 AI 编码 Agent

> 如果你是一个正在阅读本文的 AI 编码 Agent，请协助你的主人完成下述步骤：
> **获取或更新 Cloud Glyph 自身**，以便使用其技能系统。
>
> 1. **假定你的主人已经完成从 Cloud Glyph 模板仓库创建独立仓库，并将其作为 git 子模块添加到宿主仓库的 `Wiki/` 下**
>	1.1 在 `Wiki/` 子模块检出目录内工作；`Project_Root` 是宿主仓库根目录
>	1.2 执行 `python Wiki/sync_template.py` 将模板文件同步进子模块
>	1.3 若你是 Claude，可运行 `python Wiki/skills/claude_install.py <宿主仓库根目录> --lang <en|zh>`，技能将安装到 `<宿主仓库根目录>/.claude/`
>	1.4 非 Claude 用：`python Wiki/skills/gen_skill.py --lang <en|zh>` 输出 `Wiki/skills/SKILL.md`，并按你自己的规范去处置这个文件
> 2. **如果你是基于任何工具、MCP 服务远程访问到这个文件而无本地仓库**
>	2.1 告诉用户从本模板创建自己的仓库，并把它作为 `Wiki/` 子模块加入宿主仓库（见“人类快速上手”）
>	2.2 确认用户操作完成后再返回到第一种情况并执行

---

## 📤 发布

### 配置 GitHub Pages

在你的 Wiki 仓库的 GitHub **Settings → Pages** 中，将 **Build and deployment → Source** 设置为 **`GitHub Actions`**。

### 推送

在 `Wiki/` 子模块内提交并推送，让它自己的工作流部署 Pages：

```bash
cd Wiki
git add .
git commit -m "添加 Wiki 内容"
git push origin master
```

然后回到宿主仓库根目录，提交更新后的子模块指针：

```bash
git add Wiki
git commit -m "更新 Wiki 子模块"
git push
```

你的发布站点地址为：

```
https://<你的用户名>.github.io/MyProject-Wiki/
```

> **自动部署：** Wiki 仓库的 GitHub Actions 工作流在 `src/**`（内容或查看器代码）或包版本发生变化时自动触发。

---

## 🔄 保持技能更新

CloudGlyph 的 `skills/` 目录可能会收到更新。在宿主仓库根目录执行，把最新模板同步进 `Wiki/` 子模块，同时保留已编写的文档：

```bash
python Wiki/sync_template.py
```

该脚本会从 GitHub 拉取最新模板，把所有文件（skills、配置、工作流等）同步进子模块，并保留 `src/CloudGlyph/Assets/Docs/content/` 下你已有的内容。

同步后，在子模块中为每种语言重新生成 SKILL：

```bash
python Wiki/skills/gen_skill.py --lang en
python Wiki/skills/gen_skill.py --lang zh
```

如果使用 Claude，在宿主仓库根目录重新安装：

```bash
python Wiki/skills/claude_install.py <宿主仓库根目录> --lang en
```

按“发布”一节在 `Wiki/` 内提交并推送。