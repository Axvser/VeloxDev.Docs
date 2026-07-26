# 技术栈分析

## 职责

深入分析目标代码库，识别技术栈、入口点、模块结构和依赖链。此技能为后续所有文档编写提供基础认知。

## 分析步骤

### 1. 识别项目类型

检查根目录的特征文件来确定技术栈：

| 特征文件 | 技术栈 |
|---|---|
| `.slnx` / `.csproj` | .NET |
| `Cargo.toml` | Rust |
| `package.json` + `tsconfig.json` | TypeScript |
| `package.json`（无 tsconfig） | JavaScript |
| `pyproject.toml` / `setup.py` | Python |
| `go.mod` | Go |
| `CMakeLists.txt` | C/C++ |
| `pom.xml` / `build.gradle` | Java |

### 2. 读取入口文件

找到并读取应用的启动文件（如 `Program.cs`、`main.rs`、`index.ts`、`main.py`），理解引导流程。

### 3. 映射模块结构

逐层分析目录，不依赖目录名猜测，而是读取每个目录中的代表性文件来确认其职责。

### 4. 构建依赖关系

读取项目/包定义文件，记录外部依赖及其用途。

## 示例

```
项目: MyApp (C# .NET 8)
├── src/
│   ├── MyApp.Core/       ← 实体、领域服务
│   │   ├── Models/       ← 数据模型
│   │   └── Services/     ← 业务逻辑
│   └── MyApp.Web/        ← ASP.NET Core Web API
│       ├── Controllers/  ← API 端点
│       └── Middleware/   ← 管道中间件
├── tests/
│   └── MyApp.Tests/      ← xUnit 测试
└── docs/                 ← 文档目录

依赖: ASP.NET Core 8.0, Entity Framework Core, Serilog
```

## 输出

- 技术栈清单（语言、框架、运行时）
- 模块职责表（每个目录的确认用途）
- 依赖关系图

## Reading Strategy

1. **Identify project type** — Check `.sln`/`.csproj`/`package.json`/`package-lock.json`/`Cargo.toml`/`go.mod`/`pyproject.toml` to identify language and framework
2. **Start from the entry point** — `Program.cs`/`main.rs`/`index.ts`/`main.py`/`cmd/` etc.
3. **Follow the dependency chain** — From core model → service layer → API/Controller layer → UI layer
4. **Look at tests** — `*Test*/`/`*Spec*`/`tests/` directories reveal expected behavior and API usage

## Key Deliverables (Structured Notes)

| Item | Description | Downstream Consumer |
|---|---|---|
| Project type & tech stack | Language, framework, build tools | api-docs, se-analysis |
| Directory structure & module responsibilities | What each directory/project does | se-analysis |
| Entry points & core flow | How the app starts and requests flow | se-analysis |
| Public API list | Key exposed interfaces and classes | api-docs |
| Test directories & patterns | Test organization and assertion style | api-docs, se-analysis |
| Third-party dependencies | Key external dependencies and their purpose | All analysis phases |

## Role in the Default Path

- The output of this phase is **structured notes**, not written directly to the Wiki
- Notes are consumed as input by Phase 6 (API Docs) and Phase 7 (SE Analysis)
- Upon completion, auto-advance to Phase 3: `lang-constraints/SKILL.md`
