# Software Engineering Analysis

## Responsibility

Produce rigorous software engineering analysis documentation. Use **PlantUML** for API call sequence diagrams, **Mermaid** for class hierarchies and architecture flowcharts, and **KaTeX** for algorithm complexity.

## Mandatory Rules

- Every code snippet **must come from an actual file**, with file path and line range noted
- All diagrams must pass syntax validation (Mermaid/PlantUML/KaTeX)
- Do not fabricate method signatures, class names, or execution flows
- If code is inferred (no example available), it must be explicitly marked as such

## Page Plan

The Architecture section is organized into the following pages. Each page after 3-2 uses **sub-pages grouped by functional module/feature** (discovered in the Module Discovery phase), so each feature gets its own dedicated analysis.

| Page | Content | Rendering | Sub-page strategy |
|---|---|---|---|
| `0_file_structure/index.md` | Repository layout, directory tree, project-to-folder mapping | Mermaid flowchart + tree | Single overview page |
| `1_functional_structure/index.md` | Module responsibility boundaries, feature-to-project mapping, entry point identification | Mermaid flowchart + tables | Single overview page |
| `2_design_patterns/index.md` | **Design pattern analysis** — one sub-page per feature/module | Mermaid classDiagram + tables | `2_design_patterns/{Feature}/index.md` — one sub-page per feature |
| `3_data_flow/index.md` | **Data flow analysis** — sequence diagrams for each feature's API call chain | **PlantUML** sequence diagrams | `3_data_flow/{Feature}/index.md` — one sub-page per feature |
| `4_complexity/index.md` | **Complexity analysis** — time/space complexity for each feature's core operations | KaTeX + tables | `4_complexity/{Feature}/index.md` — one sub-page per feature |

### Page Detail

**0_file_structure** — Repository layout showing all source directories, test directories, example directories, and their relationships. One static tree view.

**1_functional_structure** — Which features exist and which projects own them. Tables mapping feature → owning project → dependencies.

**2_design_patterns/{Feature}/index.md** — For each feature module (e.g. MVVM, AOP, Workflow), analyze the design patterns employed. Mermaid class diagrams showing interfaces, base classes, and concrete implementations. Identify patterns such as: Command Pattern (VeloxCommand), Proxy Pattern (AOP), Observer Pattern (VeloxProperty), Strategy Pattern (Eases), Template Method (TransitionCore), etc.

**3_data_flow/{Feature}/index.md** — For each feature module, produce PlantUML sequence diagrams showing the complete call chain for core API operations. Cover: normal flow, error/exception paths, and async/event-driven scenarios where applicable.

**4_complexity/{Feature}/index.md** — For each feature module, analyze the time and space complexity of its core operations. Use KaTeX for formulas. Cover: construction, execution, look-up, serialization, and memory usage. Example: `O(n)` for linear operations, `O(log n)` for spatial hash lookups, `O(1)` for property access.

## API Call Sequence Diagrams (PlantUML)

This is the **core deliverable** of this skill. For each core API endpoint, produce a PlantUML sequence diagram showing the complete call chain.

### Basic REST API Scenario

```plantuml
@startuml
!theme plain

actor User as User
participant "Controller" as Ctrl
participant "Service" as Svc
participant "Repository" as Repo
database "Database" as DB

User -> Ctrl: GET /api/users/{id}
activate Ctrl

Ctrl -> Svc: GetUserAsync(id)
activate Svc

Svc -> Repo: FindByIdAsync(id)
activate Repo

Repo -> DB: SELECT * FROM Users WHERE Id = @id
activate DB
DB --> Repo: User entity
deactivate DB

Repo --> Svc: User?
deactivate Repo

alt User exists
	Svc --> Ctrl: 200 OK + User
else User not found
	Svc --> Ctrl: 404 Not Found
end

Ctrl --> User: JSON response
deactivate Ctrl
@enduml
```

### With Middleware Pipeline

```plantuml
@startuml
!theme plain

actor Client as Client
participant "Middleware A\\n(Auth)" as Auth
participant "Middleware B\\n(Logging)" as Log
participant "Controller" as Ctrl
participant "Service" as Svc
collections "DbContext" as Db

Client -> Auth: HTTP Request
activate Auth

Auth -> Auth: Validate JWT Token
alt Invalid token
	Auth --> Client: 401 Unauthorized
	deactivate Auth
	note right: Pipeline short-circuits
else Valid token
	Auth -> Log: Forward request
	deactivate Auth
	activate Log

	Log -> Log: Log request
	Log -> Ctrl: Invoke Action
	activate Ctrl

	Ctrl -> Svc: Execute business logic
	activate Svc
	Svc -> Db: Query/Write
	activate Db
	Db --> Svc: Result
	deactivate Db
	Svc --> Ctrl: Business result
	deactivate Svc

	Ctrl --> Log: ActionResult
	deactivate Ctrl
	Log --> Client: HTTP Response
	deactivate Log
end
@enduml
```

### Async/Event-Driven Scenario

```plantuml
@startuml
!theme plain

actor User as User
participant "API" as Api
queue "Message Queue" as MQ
participant "Event Handler" as Handler
participant "Service" as Svc
database "Database" as DB

User -> Api: POST /api/orders
activate Api
Api -> DB: Save order
activate DB
DB --> Api: order_id
deactivate DB
Api -> MQ: Publish OrderCreated event
Api --> User: 202 Accepted + order_id
deactivate Api

== Async Processing ==
MQ -> Handler: Consume OrderCreated
activate Handler
Handler -> Svc: ProcessPayment(order_id)
activate Svc
Svc -> DB: Update payment status
activate DB
DB --> Svc: Done
deactivate DB
Svc --> Handler: Payment result
deactivate Svc
Handler --> MQ: ACK
deactivate Handler
@enduml
```

### PlantUML Syntax Validation Checklist

- [ ] `@startuml` / `@enduml` are paired
- [ ] All participants (`actor` / `participant` / `database` / `queue` / `collections`) are declared before use
- [ ] `activate` / `deactivate` are paired with no omissions
- [ ] `alt` / `else` / `end` block structure is correct
- [ ] `note right` / `note left` have clear scope
- [ ] `== Section Title ==` is used for phase separation

## Class Diagram (Mermaid)

```mermaid
classDiagram
	class IUserService {
		<<interface>>
		+GetUserAsync(int id) Task~User?~
		+CreateUserAsync(User user) Task~User~
	}
	class UserService {
		-IUserRepository _repo
		-ILogger _logger
		+GetUserAsync(int id) Task~User?~
		+CreateUserAsync(User user) Task~User~
	}
	class UserController {
		+GetUser(int id) IActionResult
		+CreateUser(CreateUserRequest req) IActionResult
	}
	IUserService <|.. UserService
	UserController --> IUserService
```

> Source: `src/MyApp.Web/Services/UserService.cs` lines 15-45

## Flowchart (Mermaid)

```mermaid
flowchart TD
	A[Receive HTTP Request] --> B{Auth Passed?}
	B -->|No| C[Return 401]
	B -->|Yes| D[Execute Middleware Pipeline]
	D --> E{Route Matched?}
	E -->|No| F[Return 404]
	E -->|Yes| G[Invoke Controller]
	G --> H[Execute Action]
	H --> I[Serialize JSON]
	I --> J[Return Response]
```

## Output Location

Base page: `content/{lang}/{category}/architecture/index.md`
Sub-pages: `content/{lang}/{category}/architecture/{page_group}/{Feature}/index.md`

For **Single project** tier: `content/{lang}/architecture/{page_group}/{Feature}/index.md`
For **Multi project** tier: `content/{lang}/{project}/architecture/{page_group}/{Feature}/index.md`
For **Framework/Monorepo** tier: `content/{lang}/{category}/architecture/{page_group}/{Feature}/index.md`

## Post-Write Action

After writing SE Analysis content:

- [ ] **Regenerate navigation index** — Run the tree generator script (e.g. `python gen_tree.py`) to rebuild tree.json
- [ ] **Build the project** — Run `dotnet build` to verify the new content embeds correctly
