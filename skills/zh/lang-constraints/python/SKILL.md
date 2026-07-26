# Python 文档约定

## 适用场景

检测到 `pyproject.toml` / `setup.py` / `requirements.txt` 时加载此约束。

## 约束规则

### API 文档风格

使用 Google 风格 docstrings：

```python
def add(a: int, b: int) -> int:
    """计算两个数的和。

    Args:
        a: 第一个加数
        b: 第二个加数

    Returns:
        a 与 b 的和

    Raises:
        OverflowError: 结果超出 int 范围时
    """
    result = a + b
    if not (-2**63 <= result < 2**63):
        raise OverflowError(f"{a} + {b} 溢出")
    return result
```

### 包结构

```
my_package/
├── __init__.py        # 公开 API 导出
├── core/
│   ├── __init__.py
│   └── math.py
└── cli/               # console_scripts 入口
    └── main.py
```

### 异步模式

```python
import asyncio
from typing import Optional

async def fetch_user(user_id: int, timeout: Optional[float] = None) -> dict:
    """异步获取用户信息。"""
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(f"/api/users/{user_id}") as resp:
            return await resp.json()
```

### 命名约定

| 范围 | 约定 |
|---|---|
| 函数/变量 | `snake_case` |
| 类 | `PascalCase` |
| 常量 | `UPPER_SNAKE_CASE` |
| 私有成员 | `_prefix` 下划线开头 |
