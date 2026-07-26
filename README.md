<h1 align="center">Cloud Glyph</h1>

<p align="center">
  Built with <a href="https://www.avaloniaui.net/">Avalonia UI</a> framework
</p>

<p align="center">
  <strong>Agent Write → One-Click Deploy to GitHub Pages</strong>
  <br />
  AI Agent writes Wiki via <code>skills/</code> instructions → CloudGlyph builds → Auto-publish to Pages
</p>

<p align="center">
  <a href="README.zh.md">🇨🇳 中文版本</a>
</p>

---

> **🌐 Live site:** [https://axvser.github.io/CloudGlyph/](https://axvser.github.io/CloudGlyph/)
>
> Use this template and follow this guide to get your own Agent-driven Wiki site.

---

## 🤖 Agent Instructions

> **If you are an AI coding agent reading this README:** your task is to build Wiki documentation using this skill system.
>
> Read **`skills/SKILL.md`** and follow the pipeline.

---

## 🚀 Two Usage Modes

This template supports two deployment modes. The Agent detects which mode you're in automatically.

| Mode | Scenario | Agent Behavior |
|---|---|---|
| **Nested** | Wiki repo cloned **inside** your project as a subdirectory | Auto-discovers your project and documents it (excludes itself) |
| **Standalone** | Wiki repo used independently (no surrounding project) | Asks you to provide the project path to document |

---

## 📁 Mode 1: Nested (Wiki Inside Your Project)

Clone the Wiki repo into your project as a subdirectory. The Agent accesses both your source code and the Wiki instructions from a single workspace.

### Setup

```bash
# In your project repo, create a branch for Wiki work
git checkout -b docs/wiki-content

# Clone your Wiki repo as a subdirectory
git clone https://github.com/<your-username>/MyProject-Wiki.git docs/wiki
```

Your project structure:

```
your-main-project/                     ← Your actual code (Agent documents this)
├── src/
├── tests/
├── docs/wiki/                         ← Your Wiki repo (Agent excludes this from docs)
│   ├── skills/
│   │   ├── SKILL.md                   ← Entry point
│   │   └── ...
│   └── src/CloudGlyph/Assets/Docs/content/
└── README.md
```

> **⚠️ .gitignore risk:** If your `.gitignore` contains patterns like `src/` or `**/Docs/**`, the Wiki output files may become invisible. Add `!docs/wiki/**` to exempt the Wiki directory.

### Command Your Agent

> "Read `docs/wiki/skills/SKILL.md` and follow the pipeline."

---

## 🏠 Mode 2: Standalone (Wiki as a Separate Repo)

Use the Wiki repo on its own — for example, to document a project whose source code you want to keep separate.

### Setup

Open this repository in your workspace (no project nesting needed). Optionally place the target project alongside it.

### Command Your Agent

> "Read `skills/SKILL.md` and follow the pipeline."

The Agent will detect **Standalone** mode and ask you for the project path to document.

---

## 📤 Publish

### 1. Configure GitHub Pages

In your Wiki repo's GitHub **Settings → Pages**, set **Build and deployment → Source** to **`GitHub Actions`**.

### 2. Push

```bash
cd docs/wiki       # or your wiki path
git add .
git commit -m "Add Wiki content"
git push origin master
```

Your published site will be at:

```
https://<your-username>.github.io/MyProject-Wiki/
```

> **Auto-deploy:** The GitHub Actions workflow triggers on pushes to `src/CloudGlyph/Assets/Docs/**`.

---

## 🔄 Keeping Skills Updated

CloudGlyph's `skills/` directory may receive updates. To sync your Wiki repo with the latest upstream template while preserving your written documentation:

```bash
cd <your-wiki-path>
python sync_template.py
```

The script will fetch the latest template from GitHub, synchronize all files (skills, configs, workflows), and preserve your existing content under `src/CloudGlyph/Assets/Docs/content/`.

> **Note:** `sync_template.py` is a **user-facing** tool. After syncing, regenerate the skill index for each language:
>
> ```bash
> python skills/gen_skill.py --lang en
> python skills/gen_skill.py --lang zh
> ```
>
> `gen_skill.py` is an internal development tool.
</p>