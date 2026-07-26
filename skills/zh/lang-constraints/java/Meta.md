
[#description]
Java 文档约定

[#rules]
- API 文档风格: Javadoc（`/** */`）标准，记录所有 public/protected 成员
- 构建系统: 记录 Maven（`pom.xml`）或 Gradle（`build.gradle`）配置和生命周期
- 依赖注入: 记录 DI 框架（Spring / Jakarta / Micronaut / Quarkus / Guice）和 bean 配置风格
- 注解处理: 记录注解处理器（Lombok、MapStruct 等）及其影响
- 响应式: 记录响应式栈（WebFlux / RxJava / Project Reactor）vs 命令式
- 测试: 注明测试框架（JUnit 5 / TestNG）和 mock 库（Mockito / EasyMock）
- 命名约定: `camelCase` 方法/变量，`PascalCase` 类/接口，`SCREAMING_SNAKE_CASE` 常量
