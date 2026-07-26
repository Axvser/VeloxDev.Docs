# 部署模式检测与变量确认

## 职责

在开始编写 Wiki 之前，Agent 必须明确工作上下文，并判断当前部署模式。此技能指导 Agent 检测运行环境、收集和确认所有必要的环境变量。

## 操作流程

### 1. 确定 Wiki_Root

`Wiki_Root` 是 `skills/` 目录的父目录，即 Cloud Glyph Wiki 仓库的根目录。

```
# skills/ 位于 /path/to/repo/skills/
Wiki_Root = /path/to/repo
```

### 2. 检测部署模式（Deploy_Mode）

检查 Wiki_Root 的**父目录**是否存在解决方案文件（`.slnx` / `.sln`）：

```
Wiki_Root = /path/to/repo
├── skills/
├── src/CloudGlyph/   ← Wiki 自身的源码，不应被文档化

# 检查 /path/to 下是否有 .slnx / .sln
# 如果存在 → nested 模式
# 如果不存在 → standalone 模式
```

#### 若检测为 `nested` 模式

Wiki 仓库被作为子目录克隆到某个项目中。Agent 应：
- **Solution_Root** = 父目录中的解决方案文件所在目录（即 Wiki_Root 的父目录）
- **Project_List** = 扫描 Solution_Root 下所有项目文件（`.csproj` / 等效文件），但**排除** Wiki_Root 自身（即排除 CloudGlyph 项目本身）
- Wiki 文档应描述父项目，而非 Wiki 自身

```
# 示例：nested 模式
your-main-project/             ← Solution_Root（父项目）
├── src/
│   ├── MyApp.Core/
│   └── MyApp.Web/
├── tests/
├── docs/wiki/                 ← Wiki_Root（CloudGlyph 仓库）
│   ├── skills/
│   ├── src/CloudGlyph/        ← 排除，不加入 Project_List
│   └── ...
└── MyApp.slnx                 ← 检测到此文件

Solution_Root = /path/to/your-main-project
Project_List  = ["src/MyApp.Core", "src/MyApp.Web", "tests/MyApp.Tests"]  
              # 不包含 docs/wiki/src/CloudGlyph
```

#### 若检测为 `standalone` 模式

Wiki 仓库独立使用，周围没有待文档化的项目。Agent **无法自动发现**被文档化的项目，必须：

1. 告知用户当前为 Standalone 模式
2. 请用户提供待文档化项目的路径（绝对路径或相对于 Wiki_Root 的路径）
3. 用户提供路径后，将其设为 **Solution_Root**
4. 扫描该路径下的解决方案文件并构建 **Project_List**

```
# 示例：standalone 模式
Wiki_Root = /path/to/wiki-repo
Agent 询问用户 → 用户提供 /home/user/projects/MyApp

Solution_Root = /home/user/projects/MyApp
Project_List  = ["src/MyApp.Core", "src/MyApp.Web"]
```

### 3. 确定 Language_List

- 先用交互工具（如果有）让用户多选 Wiki 的目标语种；无交互工具则直接询问用户
- 确认后将用户选择的语种列表设为 **Language_List**
- 比对 `{Wiki_Root}/src/CloudGlyph/Assets/Docs/config/languages.json` 检查是否存在未知语种
- 如果存在 `languages.json` 中未收录的语种，**不中断编写流程**，记录差异并在全部流程结束后告知用户

## 示例

### nested 模式

```
# Wiki_Root = /home/user/projects/MyApp/docs/wiki
# 检测到 /home/user/projects/MyApp/MyApp.slnx → nested

Wiki_Root     = /home/user/projects/MyApp/docs/wiki
Deploy_Mode   = nested
Solution_Root = /home/user/projects/MyApp
Project_List  = ["src/MyApp.Core", "src/MyApp.Web", "tests/MyApp.Tests"]
Language_List = ["en", "zh"]
```

### standalone 模式

```
# Wiki_Root = /home/user/projects/MyWikiRepo
# 未检测到父目录的 .slnx → standalone
# Agent 询问用户后获得项目路径

Wiki_Root     = /home/user/projects/MyWikiRepo
Deploy_Mode   = standalone
Solution_Root = /home/user/projects/SomeProject   # 由用户提供
Project_List  = ["src/SomeApp"]                    # 从用户提供的项目扫描
Language_List = ["en", "zh"]
```

## 输出

Agent 应将以上变量记录在工作内存中，后续所有文档操作均基于这些变量。
