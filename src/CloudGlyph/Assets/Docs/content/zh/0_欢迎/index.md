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

  <!-- 项目名称与描述 -->
  <h1 class="cg-title">
    <span class="gradient-text">VeloxDev</span>
  </h1>
  <p class="cg-subtitle">
    在任何 .NET GUI 上构建现代、可由 AI 操控的工作流编辑器 —— WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium
  </p>

  <hr class="gradient-rule" />

  <!-- 三步工作流 -->
  <div class="cg-steps">
    <div class="step-card cg-step" style="animation-delay: 0s;">
      <div class="step-icon" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">⛓️</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">设计</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>Workflow · Tree · Node · Slot</code></div>
    </div>
    <div class="step-card cg-step" style="animation-delay: 0.12s;">
      <div class="step-icon-delayed" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🤖</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">自动化</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>60+ Agent 工具 · MCP</code></div>
    </div>
    <div class="step-card cg-step" style="animation-delay: 0.24s;">
      <div class="step-icon-slow" style="font-size: clamp(1.4em, 4vw, 2em); margin-bottom: 6px;">🚀</div>
      <div style="font-weight: 600; font-size: clamp(0.8em, 2vw, 0.95em);">运行</div>
      <div style="font-size: clamp(0.65em, 1.6vw, 0.78em); opacity: 0.7; margin-top: 4px;"><code>WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium</code></div>
    </div>
  </div>

  <!-- 功能网格 -->
  <div class="cg-feats">
    <div class="feat-card cg-feat" style="animation-delay: 0s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">⛓️</span> 工作流<br><span style="opacity: 0.6;">Tree · Node · Slot · Link · 撤销/重做</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.05s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🤖</span> Workflow Agent<br><span style="opacity: 0.6;">60+ 工具 · MCP · 编译器</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.1s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🪶</span> MVVM<br><span style="opacity: 0.6;">源生成器 · 异步命令</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.15s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎞️</span> 过渡动画<br><span style="opacity: 0.6;">插值 · 缓动 · 流式 API</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.2s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🎨</span> 主题<br><span style="opacity: 0.6;">运行时切换 · 动画过渡</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.25s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🌀</span> AOP<br><span style="opacity: 0.6;">切面代理 · 前置/覆盖/后置</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.3s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">⚙️</span> MonoBehaviour<br><span style="opacity: 0.6;">帧驱动循环 · Tick 模拟</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.35s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">📎</span> 弱引用类型<br><span style="opacity: 0.6;">WeakDelegate · WeakQueue · WeakStack · WeakCache</span>
    </div>
    <div class="feat-card cg-feat" style="animation-delay: 0.4s;">
      <span class="feat-icon" style="font-size: 1.3em; margin-right: 6px;">🧩</span> 适配器<br><span style="opacity: 0.6;">7 个 GUI —— WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium</span>
    </div>
  </div>

  <p style="opacity: 0.4; font-size: 0.85em; margin-top: 1em;">
    <span class="glow-dot" style="background: #4a9eff; animation-delay: 0s;"></span>
    Agent 友好
    <span class="glow-dot" style="background: #a78bfa; animation-delay: 0.3s;"></span>
    无需数据库
    <span class="glow-dot" style="background: #f472b6; animation-delay: 0.6s;"></span>
    开源 · MIT
  </p>
</div>

这是 **VeloxDev** 的文档站点——一个用于构建**交互式工作流编辑器**的 .NET 基础框架。单一模型连同编译期身份与编译执行引擎（`CompilerEx`）都位于零 UI 依赖的 `VeloxDev.Core` 中；平台适配器只提供视图；函数调用型 **Workflow Agent**（外加可选的 MCP）让 LLM 成为一流的图控制器，并与 GUI 共享撤销/重做、校验与生命周期。

**仓库** —— 源码：[github.com/Axvser/VeloxDev](https://github.com/Axvser/VeloxDev) · 在线 Wiki：[axvser.github.io/VeloxDev.Docs](https://axvser.github.io/VeloxDev.Docs/)（WebAssembly 应用，加载速度取决于网络）。

## 浏览文档

Wiki 有五个维度，每个维度均提供中文与英文版本。从本页出发，其余四个维度位于上一级目录：

| 维度 | 内容 |
|---|---|
| **欢迎** | 本页——项目介绍与后续导航 |
| [快速开始](../1_快速开始/index.md) | 每个功能一份可运行、端到端的上手教程 |
| [API](../2_API/index.md) | 已文档化公开类型与成员的完整参考 |
| [SE分析](../3_SE分析/index.md) | 文件/功能结构、设计模式、数据流、复杂度 |
| [版权](../4_版权/index.md) | 许可证信息与归属 |

## 已文档化的九个功能

九个功能均已文档化，并各自在快速开始、API 与 SE 分析三棵树中保持一致覆盖：

| 功能 | 提供的特性 |
|---|---|
| [工作流系统](../1_快速开始/00_工作流系统/index.md) | Tree / Node / Slot / Link 模型，含撤销/重做、空间索引、深度缩放画布数学、序列化与编译执行引擎（正向 + 反向） |
| [工作流代理](../1_快速开始/01_工作流代理/index.md) | 60+ 函数调用工具 + MCP——AI 可在运行时检查、构建并修改图 |
| [MVVM](../1_快速开始/02_MVVM/index.md) | 为可观察属性与可异步取消的命令提供源生成器 |
| [过渡动画](../1_快速开始/03_过渡动画/index.md) | 跨平台插值动画，含缓动与流式 API |
| [动态主题](../1_快速开始/04_动态主题/index.md) | 带动画过渡的运行时主题切换 |
| [AOP](../1_快速开始/05_AOP/index.md) | 拦截节点执行的编译期切面代理 |
| [MonoBehaviour](../1_快速开始/06_MonoBehaviour/index.md) | 面向 Tick 模拟的帧驱动生命周期循环 |
| [弱引用类型](../1_快速开始/07_弱引用类型/index.md) | `WeakDelegate` · `WeakQueue` · `WeakStack` · `WeakCache` |
| [平台适配器](../1_快速开始/08_平台适配器/index.md) | 七个视图层——WPF · Avalonia · WinUI · MAUI · WinForms · Razor · Jalium |
