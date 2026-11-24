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

1. **Create your Wiki repo** from this template on GitHub ("Use this template")
2. In the host repo where CloudGlyph should build a Wiki (convention: its root), add your wiki repo as a git submodule:

   ```bash
   git submodule add <your-wiki-repo-url> Wiki
   ```

3. **Tell your Agent** to read this README
4. **Push inside `Wiki/`** — that repo's GitHub Action auto-deploys to Pages — then commit the updated submodule pointer in the host repo

---

## 🤖 For AI Coding Agents

> If you are an AI coding agent reading this, assist your owner with the steps below:
> **obtain or update Cloud Glyph itself** so you can use its skill system.
>
> 1. **Assume your owner has already created a repo from the Cloud Glyph template and added it to the host repo as a git submodule at `Wiki/`**
>    1.1 Work inside the `Wiki/` submodule checkout; `Project_Root` is the host repo root
>    1.2 Run `python Wiki/sync_template.py` to sync the template files into the submodule
>    1.3 If you are Claude, run `python Wiki/skills/claude_install.py <host-repo-root> --lang <en|zh>` to install the SKILL into `<host-repo-root>/.claude/`
>    1.4 For non-Claude agents: `python Wiki/skills/gen_skill.py --lang <en|zh>` outputs `Wiki/skills/SKILL.md`, then handle it per your own conventions
> 2. **If you are accessing this file remotely via any tool or MCP service without a local repo**
>    2.1 Tell the user to create their own repo from this template and add it as a `Wiki/` submodule in the host repo (see Quick Start)
>    2.2 Confirm the user has done so, then return to scenario 1 and execute

---

## 📤 Publishing

### Configure GitHub Pages

In your wiki repo's GitHub **Settings → Pages**, set **Build and deployment → Source** to **`GitHub Actions`**.

### Push

Commit and push inside the `Wiki/` submodule so its own workflow deploys Pages:

```bash
cd Wiki
git add .
git commit -m "Add Wiki content"
git push origin master
```

Then, from the host repo root, commit the updated submodule pointer:

```bash
git add Wiki
git commit -m "Update Wiki submodule"
git push
```

Your published site will be at:

```
https://<your-username>.github.io/MyProject-Wiki/
```

> **Auto-deploy:** The wiki repo's GitHub Actions workflow triggers on pushes that change `src/**` (content or viewer code) or the package pins.

---

## 🔄 Keeping Skills Updated

CloudGlyph's `skills/` directory may receive updates. From the host repo root, sync the latest template into the `Wiki/` submodule while preserving your written documentation:

```bash
python Wiki/sync_template.py
```

The script fetches the latest template from GitHub, syncs all files (skills, configs, workflows) into the submodule, and preserves your existing content under `src/CloudGlyph/Assets/Docs/content/`.

After syncing, regenerate the SKILL for each language from the submodule:

```bash
python Wiki/skills/gen_skill.py --lang en
python Wiki/skills/gen_skill.py --lang zh
```

Then reinstall if using Claude (from the host repo root):

```bash
python Wiki/skills/claude_install.py <host-repo-root> --lang en
```

Commit and push inside `Wiki/` as described in Publishing.