# Deploy Mode Detection & Variable Confirmation

## Responsibility

Before writing the Wiki, the Agent must clarify the work context and determine the current deployment mode. This skill guides the Agent in detecting the runtime environment and collecting all necessary environment variables.

## Workflow

### 1. Determine Wiki_Root

`Wiki_Root` is the parent directory of `skills/`, i.e. the root of the Cloud Glyph Wiki repository.

```
# skills/ is at /path/to/repo/skills/
Wiki_Root = /path/to/repo
```

### 2. Detect Deployment Mode (Deploy_Mode)

Check if the **parent** of Wiki_Root contains a solution file (`.slnx` / `.sln`):

```
Wiki_Root = /path/to/repo
├── skills/
├── src/CloudGlyph/   ← Wiki's own source code, should NOT be documented

# Check if /path/to has .slnx / .sln
# If yes → nested mode
# If no → standalone mode
```

#### If `nested` mode

The Wiki repo is cloned as a subdirectory inside a project. The Agent should:
- **Solution_Root** = the solution file's directory (i.e. the parent of Wiki_Root)
- **Project_List** = scan all project files (`.csproj` / equivalent) under Solution_Root, but **exclude** Wiki_Root itself (exclude the CloudGlyph project)
- Wiki documentation should describe the parent project, not the Wiki itself

```
# Example: nested mode
your-main-project/             ← Solution_Root (parent project)
├── src/
│   ├── MyApp.Core/
│   └── MyApp.Web/
├── tests/
├── docs/wiki/                 ← Wiki_Root (CloudGlyph repo)
│   ├── skills/
│   ├── src/CloudGlyph/        ← Excluded from Project_List
│   └── ...
└── MyApp.slnx                 ← Detected this file

Solution_Root = /path/to/your-main-project
Project_List  = ["src/MyApp.Core", "src/MyApp.Web", "tests/MyApp.Tests"]  
			  # Does NOT include docs/wiki/src/CloudGlyph
```

#### If `standalone` mode

The Wiki repo is used independently with no surrounding project. The Agent **cannot auto-discover** the project to document, and must:

1. Inform the user they are in Standalone mode
2. Ask the user to provide the path to the project they want documented (absolute or relative to Wiki_Root)
3. Once provided, set it as **Solution_Root**
4. Scan that path for solution files and build **Project_List**

```
# Example: standalone mode
Wiki_Root = /path/to/wiki-repo
Agent asks user → user provides /home/user/projects/MyApp

Solution_Root = /home/user/projects/MyApp
Project_List  = ["src/MyApp.Core", "src/MyApp.Web"]
```

### 3. Determine Language_List

- Use interactive tools (if available) to let users multi-select Wiki target languages; otherwise ask directly
- After confirmation, set the user's selected languages as **Language_List**
- Validate against `{Wiki_Root}/src/CloudGlyph/Assets/Docs/config/languages.json` for unknown languages
- If languages are found that are not in `languages.json`, **do not interrupt the pipeline**, record the discrepancy and inform the user after all steps complete

## Examples

### nested mode

```
# Wiki_Root = /home/user/projects/MyApp/docs/wiki
# Detected /home/user/projects/MyApp/MyApp.slnx → nested

Wiki_Root     = /home/user/projects/MyApp/docs/wiki
Deploy_Mode   = nested
Solution_Root = /home/user/projects/MyApp
Project_List  = ["src/MyApp.Core", "src/MyApp.Web", "tests/MyApp.Tests"]
Language_List = ["en", "zh"]
```

### standalone mode

```
# Wiki_Root = /home/user/projects/MyWikiRepo
# No .slnx in parent directory → standalone
# Agent asks user for project path

Wiki_Root     = /home/user/projects/MyWikiRepo
Deploy_Mode   = standalone
Solution_Root = /home/user/projects/SomeProject   # Provided by user
Project_List  = ["src/SomeApp"]                    # Scanned from user's project
Language_List = ["en", "zh"]
```

## Output

The Agent should record all variables in working memory. All subsequent documentation operations are based on these variables.
