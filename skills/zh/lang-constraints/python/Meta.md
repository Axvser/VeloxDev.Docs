
[#description]
Python 文档约定

[#rules]
- API 文档风格: Google 风格或 NumPy 风格 docstrings 标准
- 类型注解: 尊重 `typing` 注解（`List[int]`、`Optional[str]`）；Python 3.10+ `X | Y` 语法
- 包结构: 记录 `pyproject.toml` / `setup.py` / `setup.cfg` 配置，展示 entry points
- 异步: 记录 `async`/`await` 模式，说明运行时（asyncio / anyio / trio）
- 测试: 记录测试框架（pytest / unittest）、fixture、覆盖率要求
- 依赖管理: 注明 pip / poetry / uv / conda，记录依赖分组
- 命名约定: `snake_case` 函数/变量，`PascalCase` 类，`UPPER_SNAKE_CASE` 常量
