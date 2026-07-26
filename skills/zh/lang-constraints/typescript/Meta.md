
[#description]
TypeScript / JavaScript 文档约定

[#rules]
- API 文档风格: JSDoc / TSDoc（`/** */`）标准
- 模块系统: 说明 ESM（`import`/`export`）或 CJS（`require`/`module.exports`）；注意 `package.json` 中的 `"type": "module"`
- 类型系统: TS 需记录 strict 级别、工具类型（`Partial<T>`、`Pick<T,K>` 等）、branded types
- 异步模式: 记录 `Promise<T>` / `async`/`await`，说明 `AbortSignal`/`AbortController` 取消
- 测试: 记录测试框架（jest / vitest / mocha）和断言库
- 构建工具: 记录打包器（webpack / vite / esbuild / tsc）及配置
- 命名约定: `camelCase` 变量/函数，`PascalCase` 类/类型/接口，`UPPER_SNAKE_CASE` 常量
