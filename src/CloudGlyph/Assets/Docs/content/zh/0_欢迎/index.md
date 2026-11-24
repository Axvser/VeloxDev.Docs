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

  /* 功能卡片本身就是一个链接。这条规则让链接不显形——卡片保留自己的颜色，且不带下划线。 */
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

  <h1 class="cg-title">
    <span class="gradient-text">VeloxDev</span>
  </h1>
  <p class="cg-subtitle">
    面向 .NET 的节点编辑器与工作流引擎框架
  </p>

  <hr class="gradient-rule" />

  <div class="cg-steps">
    <div class="step-card cg-step" style="animation-delay: 0s;">
      <div class="step-icon" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🧱</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">建模</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>树 · 节点 · 插槽 · 连线</code></div>
    </div>
    <div class="step-card cg-step" style="animation-delay: 0.12s;">
      <div class="step-icon-delayed" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🔨</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">编译</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;">链 → 分支 → 并行</div>
    </div>
    <div class="step-card cg-step" style="animation-delay: 0.24s;">
      <div class="step-icon-slow" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🚀</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">运行</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;">重试 · 重定向 · 检查点</div>
    </div>
  </div>

  <!--
    功能卡片网格。每一张卡片都是一个链接，指向它所描述的那项功能在「快速开始」中的页面——
    把卡片内容用 <a class="feat-link" href="…"> 包住即可。从 0_欢迎/index.md 出发，其余顶层
    维度都在上层目录，因此目标写作 ../{快速开始目录}/{功能目录}/index.md（当某项功能没有
    自己的快速开始页面时，../1_快速开始/index.md 这个栏目概览页也是合法目标）。目录名要带
    数字前缀；卡片文字本身就是标签，链接不再添加任何文本。
  -->
  <div class="cg-feats">
    <div class="feat-card cg-feat" style="animation-delay: 0s;">
      <a class="feat-link" href="../1_快速开始/00_工作流图模型/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🗂️</span> 工作流图模型<br><span style="opacity: 0.6;">默认视图模型 · 源生成管道</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.05s;">
      <a class="feat-link" href="../1_快速开始/04_工作流编译器/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">⚙️</span> 工作流编译器<br><span style="opacity: 0.6;">链 · 分支 · 并行片段</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.1s;">
      <a class="feat-link" href="../1_快速开始/07_画布输入与导航/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🖱️</span> 画布输入与导航<br><span style="opacity: 0.6;">平移 · 缩放 · 拖拽 · 定位</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.15s;">
      <a class="feat-link" href="../1_快速开始/09_小地图/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🗺️</span> 小地图<br><span style="opacity: 0.6;">缩略图 · 视口框 · 拖动</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.2s;">
      <a class="feat-link" href="../1_快速开始/11_MVVM视图模型生成/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">⚡</span> MVVM 视图模型生成<br><span style="opacity: 0.6;">[VeloxProperty] · [VeloxCommand]</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.25s;">
      <a class="feat-link" href="../1_快速开始/12_过渡动画/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎞️</span> 过渡动画<br><span style="opacity: 0.6;">链式声明 · 缓动 · 时间线</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.3s;">
      <a class="feat-link" href="../1_快速开始/17_工作流智能体工具/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🤖</span> 工作流智能体工具<br><span style="opacity: 0.6;">查询 · 编辑 · 执行 · 布局</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.35s;">
      <a class="feat-link" href="../1_快速开始/24_平台适配器契约/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🧩</span> 平台适配器契约<br><span style="opacity: 0.6;">一套表面 · 七家适配器</span></a>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.4s;">
      <a class="feat-link" href="../1_快速开始/32_工作流条目模板/index.md"><span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">📦</span> 工作流条目模板<br><span style="opacity: 0.6;">dotnet new · 7 个包 · 7 种角色</span></a>
    </div>
  </div>

</div>
