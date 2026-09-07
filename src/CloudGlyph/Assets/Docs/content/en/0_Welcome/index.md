<style>
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-9px); }
  }
  @keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
  }
  @keyframes pop-in {
    0% { opacity: 0; transform: scale(0.85); }
    100% { opacity: 1; transform: scale(1); }
  }
  @keyframes glow-pulse {
    0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent-color, #4a9eff) 0%, transparent); }
    50% { box-shadow: 0 0 18px 2px color-mix(in srgb, var(--accent-color, #4a9eff) 25%, transparent); }
  }

  .cg-wrapper * {
    will-change: transform, opacity;
  }

  .step-card {
    transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
                opacity 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
                box-shadow 0.35s ease;
    animation: pop-in 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  }
  .step-card:hover {
    transform: translateY(-5px) scale(1.04);
    opacity: 0.8 !important;
    box-shadow: 0 0 18px 2px color-mix(in srgb, var(--accent-color, #4a9eff) 25%, transparent);
  }

  .step-icon {
    display: inline-block;
    animation: float 3.5s ease-in-out infinite;
  }
  .step-icon-delayed {
    display: inline-block;
    animation: float 3.5s ease-in-out 0.6s infinite;
  }
  .step-icon-slow {
    display: inline-block;
    animation: float 3.5s ease-in-out 1.2s infinite;
  }

  .feat-card {
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
                opacity 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
                border-color 0.3s ease,
                box-shadow 0.3s ease;
    animation: pop-in 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  }
  .feat-card:hover {
    transform: translateY(-4px) scale(1.03);
    opacity: 0.7 !important;
    border-color: var(--accent-color, #4a9eff) !important;
    box-shadow: 0 0 14px 1px color-mix(in srgb, var(--accent-color, #4a9eff) 20%, transparent);
  }

  .feat-icon {
    display: inline-block;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .feat-card:hover .feat-icon {
    transform: scale(1.4) rotate(6deg);
  }

  .gradient-text {
    background: linear-gradient(135deg, #4a9eff, #a78bfa, #f472b6, #4a9eff);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 4s linear infinite;
  }

  .glow-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin: 0 4px;
    vertical-align: middle;
    animation: glow-pulse 1.8s ease-in-out infinite;
  }
  .gradient-rule {
    width: clamp(36px, 8vw, 60px);
    margin: 0 auto clamp(1em, 3vw, 2.2em);
    border: none;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-color, #4a9eff), #a78bfa, #f472b6);
    border-radius: 2px;
    opacity: 0.5;
  }
  .cg-wrapper {
    text-align: center;
    padding: clamp(24px, 5vw, 50px) clamp(12px, 3vw, 28px);
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
  .cg-title {
    font-size: clamp(1.6em, 6vw, 2.8em);
    margin-bottom: 0.1em;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  .cg-subtitle {
    font-size: clamp(0.9em, 2.5vw, 1.15em);
    opacity: 0.55;
    margin-bottom: clamp(0.8em, 3vw, 2em);
  }
  .cg-steps {
    display: flex;
    gap: clamp(10px, 2vw, 20px);
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: clamp(1.2em, 4vw, 2.5em);
  }
  .cg-step {
    flex: 1 1 clamp(120px, 22vw, 200px);
    padding: clamp(12px, 2vw, 18px) clamp(8px, 1.5vw, 12px);
    border-radius: 14px;
    border: 1px solid currentColor;
    opacity: 0.55;
  }
  .cg-feats {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(8px, 1.5vw, 12px);
    justify-content: center;
    text-align: left;
    margin-bottom: clamp(1em, 3vw, 2em);
  }
  .cg-feat {
    flex: 1 1 clamp(120px, 20vw, 170px);
    min-width: 100px;
    padding: clamp(8px, 1.2vw, 12px) clamp(10px, 1.5vw, 14px);
    border-radius: 10px;
    border: 1px solid currentColor;
    opacity: 0.45;
    font-size: clamp(0.75em, 1.8vw, 0.85em);
  }
</style>

<div class="cg-wrapper">

  <!-- Project name and description -->
  <h1 class="cg-title">
    <span class="gradient-text">VeloxDev</span>
  </h1>
  <p class="cg-subtitle">
    Build modern, AI-controllable workflow editors on any .NET GUI — WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium
  </p>

  <hr class="gradient-rule" />

  <!-- Three-step workflow -->
  <div class="cg-steps">
    <div class="step-card cg-step" style="animation-delay: 0s;">
      <div class="step-icon" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">⛓️</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">Design</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>Workflow · Tree · Node · Slot</code></div>
    </div>
    <div class="step-card cg-step" style="animation-delay: 0.12s;">
      <div class="step-icon-delayed" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🤖</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">Automate</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>60+ Agent tools · MCP</code></div>
    </div>
    <div class="step-card cg-step" style="animation-delay: 0.24s;">
      <div class="step-icon-slow" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🚀</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">Run</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium</code></div>
    </div>
  </div>

  <!-- Feature grid -->
  <div class="cg-feats">
    <div class="feat-card cg-feat" style="animation-delay: 0s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">⛓️</span> Workflow<br><span style="opacity: 0.6;">Tree · Node · Slot · Link · Undo/Redo</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.05s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🤖</span> Workflow Agent<br><span style="opacity: 0.6;">60+ tools · MCP · Compiler</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.1s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🪶</span> MVVM<br><span style="opacity: 0.6;">Source generators · Async commands</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.15s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎞️</span> Transition<br><span style="opacity: 0.6;">Interpolation · Easing · Fluent API</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.2s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎨</span> Theme<br><span style="opacity: 0.6;">Runtime switching · Animated</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.25s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🌀</span> AOP<br><span style="opacity: 0.6;">Aspect proxies · Start/Coverage/End</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.3s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">⚙️</span> MonoBehaviour<br><span style="opacity: 0.6;">Frame-driven loop · Tick-based</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.35s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">📎</span> Weak References<br><span style="opacity: 0.6;">WeakDelegate · WeakQueue · WeakStack · WeakCache</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.4s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🧩</span> Adapters<br><span style="opacity: 0.6;">7 GUIs — WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium</span>
    </div>
  </div>

  <p style="opacity: 0.4; font-size: 0.85em; margin-top: 1em;">
    <span class="glow-dot" style="background: #4a9eff; animation-delay: 0s;"></span>
    Agent-friendly
    <span class="glow-dot" style="background: #a78bfa; animation-delay: 0.3s;"></span>
    No DB required
    <span class="glow-dot" style="background: #f472b6; animation-delay: 0.6s;"></span>
    Open Source · MIT
  </p>
</div>

This is the documentation site for **VeloxDev** — a .NET foundation for building **interactive workflow editors**. One model with compile-time identity and a compiled execution engine (`CompilerEx`) lives in `VeloxDev.Core` with zero UI dependencies; platform adapters supply only the views; and a function-calling **Workflow Agent** (+ optional MCP) makes an LLM a first-class graph controller, sharing the GUI's undo/redo, validation and lifecycle.

**Repositories** — source code: [github.com/Axvser/VeloxDev](https://github.com/Axvser/VeloxDev) · online wiki: [axvser.github.io/VeloxDev.Docs](https://axvser.github.io/VeloxDev.Docs/) (a WebAssembly app, so its load speed depends on your network).

## Explore the documentation

The Wiki has five dimensions, each present in English and Chinese. From this page the other four dimensions are one level up:

| Dimension | Contents |
|---|---|
| **0_Welcome** | this page — the project pitch and where to go next |
| [1_QuickStart](../1_QuickStart/index.md) | runnable, end-to-end tutorials — one per feature |
| [2_API](../2_API/index.md) | full reference of every documented public type and member |
| [3_SE_Analysis](../3_SE_Analysis/index.md) | file/functional structure, design patterns, data flow, complexity |
| [4_Copyright](../4_Copyright/index.md) | license information and attribution |

## Documented features

Nine features are documented, each covered consistently across the QuickStart, API and SE Analysis trees:

| Feature | What it provides |
|---|---|
| [Workflow system](../1_QuickStart/00_workflow-system/index.md) | Tree / Node / Slot / Link model with undo-redo, spatial indexing, deep-zoom canvas math, serialization and a compiled execution engine (forward + reverse) |
| [Workflow Agent](../1_QuickStart/01_workflow-agent/index.md) | 60+ function-calling tools + MCP — an AI can inspect, build and mutate graphs at runtime |
| [MVVM](../1_QuickStart/02_mvvm/index.md) | source generators for observable properties and async, cancellable commands |
| [Transition](../1_QuickStart/03_transition/index.md) | cross-platform interpolation animation with easing and a fluent API |
| [Dynamic theme](../1_QuickStart/04_dynamic-theme/index.md) | runtime theme switching with animated transitions |
| [AOP](../1_QuickStart/05_aop/index.md) | compile-time aspect proxies to intercept node execution |
| [MonoBehaviour](../1_QuickStart/06_monobehaviour/index.md) | frame-driven lifecycle loop for tick-based simulation |
| [Weak references](../1_QuickStart/07_weak-types/index.md) | `WeakDelegate` · `WeakQueue` · `WeakStack` · `WeakCache` |
| [Platform adapters](../1_QuickStart/08_platform-adapters/index.md) | seven view layers — WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium |
