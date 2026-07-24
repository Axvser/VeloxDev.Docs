<p align="center">
  <img src="src/CloudGlyph/Assets/avalonia-logo.ico" width="64" alt="CloudGlyph" />
</p>

<h1 align="center">CloudGlyph</h1>

<p align="center">
  <strong>Agent 编写 → 一键部署 GitHub Pages</strong>
  <br />
  AI Agent 按 <code>skills/</code> 指令写入 Wiki → CloudGlyph 构建 → 自动发布 Pages
</p>

<p align="center">
  <a href="https://axvser.github.io/CloudGlyph/" target="_blank">🌐 在线示例</a> •
  <a href="README.md">🇬🇧 English</a>
</p>

  ---

> **🌐 已有线上站点：** [https://axvser.github.io/CloudGlyph/](https://axvser.github.io/CloudGlyph/)
>
> 使用本模板创建仓库后按本指南配置，立即拥有你专属的 Agent 驱动 Wiki 站点。



## 🚀 从模板仓库创建到发布

由于此仓库是一个 **GitHub 模板仓库**，你只需几步即可创建自己的 Wiki 站点，且所有 Wiki 相关文件不会干扰你的主项目代码。

### Step 1: 从模板创建 Wiki 仓库

1. 进入 [CloudGlyph](https://github.com/Axvser/CloudGlyph) 仓库页面
2. 点击 **"Use this template"** → **"Create a new repository"**
3. 选择所有者并输入仓库名称（例如 `MyProject-Wiki`）
4. 选择 **Public**（免费计划下 GitHub Pages 需要公开仓库）
5. 点击 **"Create repository from template"**

> 这个仓库将作为你独立的 Wiki 站点，与你的主项目仓库完全分离。

### Step 2: 将 Wiki 仓库克隆到你的项目目录中

将上一步创建的 Wiki 仓库作为子目录克隆到你的**现有项目**中，以便项目中的 AI Agent 能直接读取 `skills/` 指令：

```bash
# 进入你的现有项目目录
cd your-main-project

# 将 Wiki 仓库克隆到子目录（如 docs/ 或 wiki/）
git clone https://github.com/<你的用户名>/MyProject-Wiki.git docs/wiki
```

项目结构如下：

```
your-main-project/
├── src/
├── tests/
├── docs/wiki/          ← Wiki 仓库（独立 Git 历史）
│   ├── skills/         ← Agent 读取的指令
│   ├── src/CloudGlyph/Assets/Docs/content/   ← Agent 写入的位置
│   └── ...
└── README.md
```

### Step 3: 在新分支上让 Agent 编写 Wiki

建议在你项目的**新分支**上完成所有 Wiki 工作，确保主分支干净：

```bash
git checkout -b docs/wiki-content
```

现在，让项目中的 AI Agent 读取 `docs/wiki/skills/SKILL.md`，Agent 将按指令将内容写入 `docs/wiki/src/CloudGlyph/Assets/Docs/content/` 下。

### Step 4: 配置 Wiki 仓库的 GitHub Pages

进入 Wiki 仓库（`MyProject-Wiki`）的 Settings：

1. **Settings → Pages**
2. **Build and deployment → Source → 选择 `GitHub Actions`**

Pages 会自动识别工作流中的 `actions/deploy-pages@v5` 并完成部署。

### Step 5: 推送触发发布

内容编写完成后，推送 Wiki 仓库触发自动部署：

```bash
cd docs/wiki
git add .
git commit -m "Add wiki content"
git push origin master
```

- **自动触发**：推送 `src/CloudGlyph/Assets/Docs/**` 下文件变更
- **手动触发**：Actions 标签 → "Deploy Avalonia Browser to GitHub Pages" → Run workflow

首次部署后，站点地址为：

```
https://<你的用户名>.github.io/MyProject-Wiki/
```