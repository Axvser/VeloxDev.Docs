# 版权

## 职责

`发现`【Project_Root】下的版权/许可/授权/署名文件或者信息，`组织`到Wiki中

## 发现

扫描以下所有文件，将提取到的信息按分类归入对应章节

| 分类 | 扫描文件 | 提取内容 |
|---|---|---|
| **许可证信息** | `LICENSE` / `LICENSE.md` / `LICENSE.txt` | 许可证类型（MIT / Apache-2.0 / GPL-3.0 / BSD 等）、版权持有者、年份 |
| **版权声明** | `COPYRIGHT` / `COPYRIGHT.md` | 版权声明全文 |
| **贡献者** | `AUTHORS` / `AUTHORS.md` / `CONTRIBUTORS` / `CONTRIBUTORS.md` | 贡献者列表 |
| **专利授权** | `PATENTS` / `PATENTS.md` | 专利授权条款 |
| **第三方声明** | `NOTICE` / `NOTICE.md` / `NOTICE.txt` | 第三方组件版权声明，分段保留所有署名 |

## 组织

版权页按以下顺序组织各分类{type}：

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

**第三方声明**

{从 NOTICE 提取的第三方版权声明}
```

> 若未发现对应分类的文件，不要为其创建子页

> 使用拷贝、截取等操作获取原文，避免LLM幻觉

## 输出位置

Wiki_Root/content/{language}/4_版权/{type}/index.md