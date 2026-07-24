# Welcome Page — Step 8: Replace Welcome Page with Beautiful HTML Landing

> **Sub-skill.** Step 8 of the Framework Execution Pipeline. Runs after Step 7 (Review) passes.
> **Default path phase: Phase 8 (final delivery)**

> **Context:** All paths in this file (e.g. `content/en/0_Welcome/index.md`) are relative to `WIKI_ROOT` — see the master `skills/SKILL.md` §1 for `WIKI_ROOT` determination.

Replaces the generic `0_Welcome/index.md` with a visually rich, project-specific landing page using Cloud Glyph's full inline HTML + CSS rendering capabilities.

## When to Load

- Step 8 of the default pipeline (auto-loaded)
- "Make the welcome page beautiful"
- "Design a landing page"
- "Replace the welcome page"
- "Create a hero section for the Wiki"

## Mandatory Rule

**The welcome page must contain ZERO fabricated content.** Every project name, module name, feature description, icon choice, and link must be derived from actual analysis results produced in Steps 2-6. Do not invent features the project does not have.

---

## Template Reference: Cloud Glyph Welcome Page

The existing Cloud Glyph welcome page (`content/en/0_Welcome/index.md`) provides a battle-tested template. Below is an annotated summary of its structure:

### CSS Architecture

The template uses 4 key animations and a card-based responsive layout:

| CSS Component | Purpose | Customization for Your Project |
|---|---|---|
| `@keyframes float` | Gentle vertical hover on icons | Keep — universal |
| `@keyframes shimmer` | Animated gradient on title text | Keep — universal |
| `@keyframes pop-in` | Staggered entrance animation on cards | Keep — universal |
| `@keyframes glow-pulse` | Pulsing glow on decorative dots | Keep — universal |
| `.step-card` | 3-step workflow cards with hover lift | Adapt text content only |
| `.feat-card` | Feature grid with hover scale+rotate | Adapt text content only |
| `.gradient-text` | Rainbow shimmer text effect | Keep — change colors to match project brand |
| `.gradient-rule` | Thin gradient divider | Keep — change colors to match project brand |

**Key CSS techniques used** (reusable):
- `clamp(min, preferred, max)` for fluid responsive sizing
- `color-mix(in srgb, ...)` for dynamic hover effects that respect the theme
- `will-change: transform, opacity` for GPU-accelerated animations
- `cubic-bezier(0.34, 1.56, 0.64, 1)` for elastic "pop" transitions

### HTML Structure

```
<div class="cg-wrapper">                         ← Wrapper with text-align: center
  <h1 class="cg-title">
	<span class="gradient-text">{Project Name}</span>
  </h1>
  <p class="cg-subtitle">{Tagline}</p>
  <hr class="gradient-rule" />

  <!-- Section 1: How it Works / 3 Steps -->
  <div class="cg-steps">
	<div class="step-card">Step 1: {action}</div>
	<div class="step-card">Step 2: {action}</div>
	<div class="step-card">Step 3: {action}</div>
  </div>

  <!-- Section 2: Feature Grid -->
  <div class="cg-feats">
	<div class="feat-card">Feature 1: {desc}</div>
	<div class="feat-card">Feature 2: {desc}</div>
	...
  </div>

  <!-- Section 3: Footer badges -->
  <p class="glow-dot badges">{tags}</p>
</div>
```

---

## How to Write the Welcome Page for Any Project

### Step A: Gather Information from Prior Steps

| Information Source | What to Extract |
|---|---|
| Step 2 — Project Analysis | Project name, tech stack, module list (the 3-8 core modules) |
| Step 3 — Test/Demo Discovery | Key capabilities confirmed by actual code |
| Step 4 — Quick Start | The primary use case / "hello world" flow |
| Step 5 — Architecture | Architecture diagram content (can simplify for hero) |
| Step 6 — API Deep Dive | Core public API categories |
| Step 7 — Review | Corrected module names and verified feature list |

### Step B: Structure the 3-Step Workflow

The 3 steps should tell the **user's story**, not the Cloud Glyph story. For example:

| Project Type | Step 1 | Step 2 | Step 3 |
|---|---|---|---|
| **Library** | Install (`pip install / dotnet add`) | Initialize | Use |
| **Web API** | Configure | Send Request | Handle Response |
| **CLI Tool** | Install | Run Command | Parse Output |
| **Framework** | Create Project | Add Components | Build & Deploy |

### Step C: Build the Feature Grid

Each feature card must map to a **real, verified capability** from Steps 2-6. Format:

```
<div class="feat-card cg-feat">
  <span class="feat-icon">{emoji}</span> {Feature Name}<br>
  <span style="opacity: 0.6;">{short description}</span>
</div>
```

**Guidelines for feature cards:**
- **8 cards maximum** — prioritize the most distinctive capabilities
- Each card = one verified module or cross-cutting concern
- The `<br><span>` subtitle gives a concrete example or sub-feature
- Emoji should visually represent the capability

### Step D: Footer Badges

Use `glow-dot` spans to list 3-4 key project attributes:

```
<span class="glow-dot" style="background: {color1};"></span>
{Attribute 1}
<span class="glow-dot" style="background: {color2};"></span>
{Attribute 2}
```

Examples: "MIT License", "Cross-platform", "Zero dependencies", "Type-safe", "Production-ready"

---

## Section-Specific Customization

### Title & Tagline

```html
<h1 class="cg-title">
  <span class="gradient-text">{Project Name}</span>
</h1>
<p class="cg-subtitle">
  {One-line tagline} · {Key differentiator}
</p>
```

- **Project name**: from Step 2 analysis (read from csproj, package.json, Cargo.toml, etc.)
- **Tagline**: a 4-8 word description of what the project does
- **Differentiator**: the single most notable characteristic (language, platform, architecture)

### Gradient Colors

The `gradient-text` and `gradient-rule` classes use `#4a9eff, #a78bfa, #f472b6` as defaults. Customize these to match the project's brand:

```css
.gradient-text {
  background: linear-gradient(135deg, {color1}, {color2}, {color3}, {color1});
}
```

Choose colors from the project's logo, documentation, or established brand palette. If no brand colors are evident, keep the defaults.

### Staggered Animation Delays

Cards use `animation-delay` to create cascading entrance effects:

| Card Position | Delay Increment | Example |
|---|---|---|
| 1st card | `0s` | `style="animation-delay: 0s;"` |
| 2nd card | `0.05-0.12s` | `style="animation-delay: 0.05s;"` |
| 3rd card | `0.10-0.24s` | `style="animation-delay: 0.10s;"` |
| 4th card | `0.15-0.30s` | `style="animation-delay: 0.15s;"` |
| ... increment by +0.05s each | | |

---

## Validation Checklist

Before writing the welcome page, verify the source material:

- [ ] Project name is from an actual build/config file (not guessed)
- [ ] Tagline is descriptive of actual project capabilities
- [ ] Each step card maps to a real user workflow (from demos/tests)
- [ ] Each feature card corresponds to a verified module or capability
- [ ] No feature is listed that lacks evidence from Steps 2-6
- [ ] Emoji choices are thematically appropriate for the capability
- [ ] Footer badges reflect real project attributes
- [ ] Gradient colors match project brand (or defaults used)

## Output Location (relative to `WIKI_ROOT`)

- English: `content/en/0_Welcome/index.md` — always produced
- Additional languages: `content/{lang}/0_Welcome/index.md` — only for languages selected in §1 (Language Selection). Default is English only.

All language variants share the same CSS and HTML structure; only the natural language text differs. Skip any language not in the active language list.
