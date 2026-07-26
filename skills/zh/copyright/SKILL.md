# 版权

## 职责

扫描项目根目录下的所有常见版权/许可文件，按信息所属归类组织到 Wiki 版权页面中，**不遗漏任何已找到的信息**。

## 发现规则

扫描以下所有文件，将提取到的信息按分类归入对应章节：

### 分类清单

| 分类 | 扫描文件 | 提取内容 |
|---|---|---|
| **许可证信息** | `LICENSE` / `LICENSE.md` / `LICENSE.txt` | 许可证类型（MIT / Apache-2.0 / GPL-3.0 / BSD 等）、版权持有者、年份 |
| **版权声明** | `COPYRIGHT` / `COPYRIGHT.md` | 版权声明全文 |
| **贡献者** | `AUTHORS` / `AUTHORS.md` / `CONTRIBUTORS` / `CONTRIBUTORS.md` | 贡献者列表 |
| **专利授权** | `PATENTS` / `PATENTS.md` | 专利授权条款 |
| **第三方声明** | `NOTICE` / `NOTICE.md` / `NOTICE.txt` | 第三方组件版权声明，分段保留所有署名 |

> 每个分类独立扫描。如果某个分类未找到对应文件，该分类在页面中跳过，不影响其他分类的呈现。所有文件都不存在则跳过此步，不在 Wiki 中生成版权页。

## 页面结构

版权页按以下顺序组织各分类：

```markdown
---
**许可证信息**

{从 LICENSE 提取的内容}

---

**版权声明**

{从 COPYRIGHT 提取的内容}

---

**贡献者**

{从 AUTHORS / CONTRIBUTORS 提取的名单}

---

**专利授权**

{从 PATENTS 提取的内容}

---

**第三方组件声明**

{从 NOTICE 提取的第三方版权声明}
```

> 没有对应文件的分类直接从页面中移除，不保留空标题。

## 示例

### 场景：项目有 LICENSE（MIT）、AUTHORS.md、NOTICE.md

```markdown
---
**许可证信息**

版权所有 © 2024 MyApp Contributors

本项目基于 [MIT License](LICENSE) 开源。

---

**贡献者**

- Alice
- Bob
- Carol

---

**第三方组件声明**

本项目使用了以下开源组件：

### Serilog
Copyright © 2013-2024 Serilog Contributors
MIT License

### Newtonsoft.Json
Copyright © James Newton-King 2008
MIT License
```

### 场景：项目仅有 COPYRIGHT 和 PATENTS

```markdown
---
**版权声明**

Copyright (c) 2024 MyApp Inc.
All rights reserved.

---

**专利授权**

使用本软件须遵守以下专利授权条款（详见 PATENTS 文件）：
...
```

## 输出位置

`content/{lang}/{Project}/copyright/index.md`

每个语言目录下各生成一份，内容相同。

## 写入后操作

编写版权内容后：

- [ ] **重新生成导航索引** — 运行树生成脚本（如 `python gen_tree.py`）重建 tree.json
- [ ] **构建项目** — 运行 `dotnet build` 验证新内容正确嵌入
