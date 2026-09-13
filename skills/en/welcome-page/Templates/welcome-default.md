[#when] When creating the Wiki welcome page
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

  /* A feature card is a link. This rule is what keeps the link invisible as a
     link — the card keeps its own colour, with no underline. */
  .feat-link {
	display: block;
	color: inherit;
	text-decoration: none;
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

  <!-- Adjust the project name and description to the actual project -->
  <h1 class="cg-title">
	<span class="gradient-text">Cloud Glyph</span>
  </h1>
  <p class="cg-subtitle">
	AI-powered Markdown Wiki · Desktop + Browser
  </p>

  <hr class="gradient-rule" />

  <!-- Add or remove entries as appropriate -->
  <!-- Three-step workflow -->
  <div class="cg-steps">
	<div class="step-card cg-step" style="animation-delay: 0s;">
	  <div class="step-icon" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">✍️</div>
	  <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">Write</div>
	  <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>content/{lang}/**/index.md</code></div>
	</div>
	<div class="step-card cg-step" style="animation-delay: 0.12s;">
	  <div class="step-icon-delayed" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">⚙️</div>
	  <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">Build</div>
	  <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;">Auto-index → JSON</div>
	</div>
	<div class="step-card cg-step" style="animation-delay: 0.24s;">
	  <div class="step-icon-slow" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🚀</div>
	  <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">Browse</div>
	  <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;">Desktop + Browser</div>
	</div>
  </div>

  <!-- Add or remove entries as appropriate -->
  <!--
	Feature grid. EVERY card is a link to the QuickStart page of the project
	feature it names — wrap the card's content in <a class="feat-link" href="…">.
	From 0_Welcome/index.md the other top-level dimensions are one level up, so a
	destination reads ../{QuickStart directory}/{feature directory}/index.md
	(../1_QuickStart/index.md — the section overview — is a valid destination
	when a feature has no QuickStart page of its own). Directory names carry
	their numeric prefix; the card text is the label, so the link adds no text.
  -->
  <div class="cg-feats">
	<div class="feat-card cg-feat" style="animation-delay: 0s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">📝</span> Markdown<br><span style="opacity: 0.6;">Footnotes · Tables · Task lists</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.05s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🧮</span> KaTeX<br><span style="opacity: 0.6;">Inline and display math</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.1s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🔍</span> Code Highlighting<br><span style="opacity: 0.6;">highlight.js · VS Code theme</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.15s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">📊</span> Mermaid<br><span style="opacity: 0.6;">Flow · Sequence · Class · Git</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.2s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🌿</span> PlantUML<br><span style="opacity: 0.6;">Auto dark/light SVG</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.25s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">📈</span> Function Plots<br><span style="opacity: 0.6;">y = f(x) · parametric · polar</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.3s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎬</span> Video Embed<br><span style="opacity: 0.6;">Bilibili · YouTube · Vimeo</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.35s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🌐</span> Multi-language<br><span style="opacity: 0.6;">Independent directories per language</span></a>
	</div>
	<div class="feat-card cg-feat" style="animation-delay: 0.4s;">
	  <a class="feat-link" href="../1_QuickStart/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎨</span> Theme Editor<br><span style="opacity: 0.6;">RGB sliders · Live preview</span></a>
	</div>
  </div>

</div>
