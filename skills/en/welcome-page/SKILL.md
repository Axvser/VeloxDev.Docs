# Welcome Page

## Responsibility

Replace the default `0_Welcome/index.md` with a beautiful HTML landing page featuring CSS animations and card layout.

## Prerequisites

This step executes **after all content pages (Quick Start, APIs, SE Analysis, Copyright) are written, but before the Review step.** The Welcome page requires information from those pages (project name, module names, feature descriptions), so it cannot run earlier. However, it must be reviewed together with all other content.

> **Workflow position:** Step 9 (Write Welcome). Executes after all content pages exist (Steps 5-8) but before Review (Step 10). The agent should place Welcome page writing right after all content exists, immediately before Review.

## Core Rules

### No Fabrication

Everything on the welcome page must come from actual analysis results. Project name, module names, feature descriptions, icon selections, and links must all be traceable to previous steps.

### Fixed Outer Container

```html
<div class="cg-wrapper">    ← This container must not be modified
  <!-- Inner content can be customized -->
</div>
```

Forbidden: `overflow: scroll`, `max-height`, extra `<div>` wrappers, modifying `cg-wrapper`'s `text-align`/`padding`/`width`.

## Writing Steps

### Step A: Collect Information

| Source | Content to Extract |
|---|---|
| Tech stack analysis | Project name, tech stack, core module list (3-8 items) |
| Quick start | Main use-case flow |
| APIs | Core public API categories |

### Step B: Build a 3-Step Workflow

Design user stories based on project type:

| Project Type | Step 1 | Step 2 | Step 3 |
|---|---|---|---|
| Class Library | Install | Initialize | Use |
| Web API | Configure | Send Request | Handle Response |
| CLI Tool | Install | Run Command | Parse Output |
| Framework | Create Project | Add Components | Build & Deploy |

### Step C: Build Feature Grid

```html
<div class="feat-card cg-feat">
  <span class="feat-icon">⚡</span> High Performance<br>
  <span style="opacity: 0.6;">Supports 100K requests/sec</span>
</div>
```

Maximum 8 cards, each corresponding to a verified module.

### Step D: Footer Badges

```html
<span class="glow-dot" style="background: #4CAF50;"></span>
MIT License
<span class="glow-dot" style="background: #2196F3;"></span>
Cross-platform
```

## Animation Delay Table

|---|---|---|
| 1st card | `0s` | `style="animation-delay: 0s;"` |
| 2nd card | `0.05-0.12s` | `style="animation-delay: 0.05s;"` |
| 3rd card | `0.10-0.24s` | `style="animation-delay: 0.10s;"` |
| 4th card | `0.15-0.30s` | `style="animation-delay: 0.15s;"` |
| ... increment by +0.05s each | | |

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

## Post-Write Action

After writing/updating the Welcome page (and any other content page):

- [ ] **Regenerate navigation index** — Run the tree.json generator script (e.g. `python gen_tree.py`) to update the navigation tree
- [ ] **Verify tree output** — Confirm the regenerated tree.json includes all new pages and the Welcome page is the first root entry
- [ ] **Build the project** — Run a build (`dotnet build`) to verify all assets are embedded correctly and the application compiles

## Output Location (relative to `WIKI_ROOT`)

- English: `content/en/0_Welcome/index.md` — always produced
- Additional languages: `content/{lang}/0_Welcome/index.md` — only for languages selected in Step 1 (Language Selection). Default is English only.

All language variants share the same CSS and HTML structure; only the natural language text differs. Skip any language not in the active language list.
