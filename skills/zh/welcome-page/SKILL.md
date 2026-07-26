# 欢迎页

## 职责

替换默认的 `0_Welcome/index.md` 为带有 CSS 动画和卡片布局的美观 HTML 着陆页。

## 前置要求

此步骤在**所有内容页面（快速入门、API、软件工程分析、版权）编写完成后、审核步骤之前**执行。欢迎页需要引用其他页面的信息（项目名、模块名、功能描述），因此不能更早执行。但它必须与所有其他内容一起接受审核。

> **工作流位置：** 步骤 5-8（内容编写）→ 步骤 9（编写欢迎页）→ 步骤 10（审核）。Agent 应在所有内容存在后、审核之前立即编写欢迎页。

## 核心规则

### 禁止编造

欢迎页中的一切内容必须来自实际分析结果。项目名、模块名、功能描述、图标选择、链接都必须能在之前步骤中找到依据。

### 外层容器固定

```html
<div class="cg-wrapper">    ← 此容器不可修改
  <!-- 内部内容可自定义 -->
</div>
```

禁止：`overflow: scroll`、`max-height`、额外 `<div>` 包裹、修改 `cg-wrapper` 的 `text-align`/`padding`/`width`。

## 编写步骤

### Step A: 收集信息

| 来源 | 提取内容 |
|---|---|
| 技术栈分析 | 项目名、技术栈、核心模块列表（3-8 个） |
| 快速开始 | 主要用例流程 |
| APIs | 核心公开 API 分类 |

### Step B: 构建 3 步工作流

根据项目类型设计用户故事：

| 项目类型 | 步骤 1 | 步骤 2 | 步骤 3 |
|---|---|---|---|
| 类库 | 安装 | 初始化 | 使用 |
| Web API | 配置 | 发送请求 | 处理响应 |
| CLI 工具 | 安装 | 运行命令 | 解析输出 |
| 框架 | 创建项目 | 添加组件 | 构建部署 |

### Step C: 构建功能网格

```html
<div class="feat-card cg-feat">
  <span class="feat-icon">⚡</span> 高性能<br>
  <span style="opacity: 0.6;">支持每秒 10 万请求</span>
</div>
```

最多 8 个卡片，每张对应一个经过验证的模块。

### Step D: 底部徽章

```html
<span class="glow-dot" style="background: #4CAF50;"></span>
MIT License
<span class="glow-dot" style="background: #2196F3;"></span>
跨平台
```

## 输出位置


|---|---|---|
| 1st card | `0s` | `style="animation-delay: 0s;"` |
| 2nd card | `0.05-0.12s` | `style="animation-delay: 0.05s;"` |
| 3rd card | `0.10-0.24s` | `style="animation-delay: 0.10s;"` |
| 4th card | `0.15-0.30s` | `style="animation-delay: 0.15s;"` |
| ... increment by +0.05s each | | |

---

## 验证清单

编写欢迎页之前，确认源材料：

- [ ] 项目名来自实际的构建/配置文件（非猜测）
- [ ] 标语准确描述项目实际能力
- [ ] 每个步骤卡片映射到真实用户工作流（来自演示/测试）
- [ ] 每个功能卡片对应已验证的模块或能力
- [ ] 无缺乏步骤 2-6 证据的功能列出
- [ ] Emoji 选择在主题上适合该能力
- [ ] 底部徽章反映真实项目属性
- [ ] 渐变颜色匹配项目品牌（或使用默认值）

## 写入后操作

编写/更新欢迎页（以及任何其他内容页面）后：

- [ ] **重新生成导航索引** — 运行 tree.json 生成脚本（如 `python gen_tree.py`）更新导航树
- [ ] **验证 tree 输出** — 确认生成的 tree.json 包含所有新页面且欢迎页是第一个根条目
- [ ] **构建项目** — 运行 `dotnet build` 验证所有资源已正确嵌入且应用编译通过

## 输出位置（相对于 `WIKI_ROOT`）

- English: `content/en/0_Welcome/index.md` — 始终生成
- 其他语言：`content/{lang}/0_Welcome/index.md` — 仅针对步骤 1（语言选择）中选定的语言。默认为仅 English。

所有语言变体共享相同的 CSS 和 HTML 结构；仅自然语言文本不同。跳过不在活跃语言列表中的任何语言。
