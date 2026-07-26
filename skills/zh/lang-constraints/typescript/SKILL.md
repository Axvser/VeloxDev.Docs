# TypeScript / JavaScript 文档约定

## 适用场景

检测到 `package.json`（含或不含 `tsconfig.json`）时加载此约束。

## 约束规则

### API 文档风格

使用 JSDoc / TSDoc：

```typescript
/**
 * 计算两个数的和
 * @param a - 第一个加数
 * @param b - 第二个加数
 * @returns a 与 b 的和
 * @throws {RangeError} 当结果超出安全整数范围时
 */
export function add(a: number, b: number): number {
  if (!Number.isSafeInteger(a + b)) throw new RangeError('overflow');
  return a + b;
}
```

### 模块系统

说明使用 ESM 还是 CJS：

```typescript
// ESM 方式（推荐）
import { add } from './math.js';
export { add };

// 或者说明 package.json 中的 type 字段
// { "type": "module" }
```

### 类型系统（TypeScript）

```typescript
export interface User {
  id: number;
  name: string;
  email?: string;  // 可选字段
}

// 工具类型示例
type PartialUser = Partial<User>;
type UserName = Pick<User, 'name'>;
```

### 异步模式

```typescript
/**
 * 异步获取用户列表
 * @param signal - 可选的取消信号
 */
export async function fetchUsers(signal?: AbortSignal): Promise<User[]> {
  const response = await fetch('/api/users', { signal });
  return response.json();
}
```

### 命名约定

| 范围 | 约定 |
|---|---|
| 变量/函数 | `camelCase` |
| 类/类型/接口 | `PascalCase` |
| 常量（枚举） | `UPPER_SNAKE_CASE` |
| 文件 | `kebab-case` 或 `camelCase` |
