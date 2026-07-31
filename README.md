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
> Use this template to get your own Agent-driven Wiki site.

---

## 🚀 Quick Start for Humans

1. **Create your Wiki repo** from this template on GitHub
2. **Clone** it locally
3. **Tell your Agent** to read this README
4. **Push** — the GitHub Action auto-deploys to Pages

---

## 🤖 For AI Coding Agents

> If you are an AI coding agent reading this, assist your owner with the steps below:
> **obtain or update Cloud Glyph itself** so you can use its skill system.
>
> 1. **Assume your owner has already created a repo from the Cloud Glyph template and cloned it locally**
>    1.1 Run `python sync_template.py <your-wiki-path>` to sync files
>    1.2 If you are Claude, run `python <repo-root>/skills/claude_install.py <claude-dir>` to install the SKILL into `.claude/`
>    1.3 For non-Claude agents: `python <repo-root>/skills/gen_skill.py --lang <en|zh>` to output `skills/SKILL.md`, then handle it per your own conventions
> 2. **If you are accessing this file remotely via any tool or MCP service without a local repo**
>    2.1 Tell the user to create their own repo from this template and clone it locally
>    2.2 Confirm the user has done so, then return to scenario 1 and execute

---

## 📤 Publishing

### Configure GitHub Pages

In your Wiki repo's GitHub **Settings → Pages**, set **Build and deployment → Source** to **`GitHub Actions`**.

### Push

```bash
cd <your-wiki-path>
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
python sync_template.py <your-wiki-path>
```

The script will fetch the latest template from GitHub, synchronize all files (skills, configs, workflows), and preserve your existing content under `src/CloudGlyph/Assets/Docs/content/`.

After syncing, regenerate the SKILL for each language:

```bash
python skills/gen_skill.py --lang en
python skills/gen_skill.py --lang zh
```

Then reinstall if using Claude:

```bash
python skills/claude_install.py <claude-working-dir> --lang en
```
```