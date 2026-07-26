# Java 文档约定

## 适用场景

检测到 `pom.xml` / `build.gradle` / `build.gradle.kts` 时加载此约束。

## 约束规则

### API 文档风格

使用 Javadoc：

```java
/**
 * 计算两个数的和。
 *
 * @param a 第一个加数
 * @param b 第二个加数
 * @return a 与 b 的和
 * @throws ArithmeticException 如果结果溢出 int 范围
 */
public int add(int a, int b) {
    return Math.addExact(a, b);  // 溢出时抛异常
}
```

### DI 框架

说明使用的依赖注入框架和 bean 风格：

```java
// Spring Boot — 注解风格
@Service
public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

### 测试

```java
// JUnit 5 + Mockito
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository repository;

    @InjectMocks
    private UserService service;

    @Test
    void shouldCreateUser() {
        when(repository.save(any())).thenReturn(new User(1, "test"));
        User result = service.createUser("test");
        assertEquals(1, result.getId());
    }
}
```

### 命名约定

| 范围 | 约定 |
|---|---|
| 类/接口 | `PascalCase` |
| 方法/变量 | `camelCase` |
| 常量 | `SCREAMING_SNAKE_CASE` |
| 包名 | `all.lowercase.separated.by.dots` |
