# 快速开始

## 职责

为每个功能模块编写 Quick Start 指南，展示最简单、最声明式的使用方式。

## 编写原则

### 找到最简单入口

对于每个模块，按以下严格优先层级发现最简声明式用法：

> **优先级 1 — Demo/示例项目**
> 搜索模块的 `Examples/` 或 `samples/` 目录，**完整读取所有源文件**，查找真实的使用代码。Demo 项目展示了 API 的预期使用方式和最惯用的模式。从这些文件中提取最小化设置和使用代码。不得仅阅读部分文件就开始编写。
>
> **优先级 2 — 单元测试**
> 如果某模块没有 Demo，**完整读取所有测试文件**，扫描其测试项目中的测试方法，提取参数构造、方法调用和断言模式。
>
> **优先级 3（兜底）— 源码接口自行发现**
> 仅在 Demo 和测试都不存在时：从源码文件中读取公共 API 签名并构造最小使用示例。标注为*推断所得*。

### 最简 vs 详细模式

对于每个 API，识别其最简声明式用法。当存在多种用法模式时（如扩展方法、Fluent API、基于特性的方式和底层接口派生），Quick Start **必须优先采纳最上层、最封装的 API**——即用户需要写最少样板代码的那种。扩展方法、Fluent API 和基于特性的模式优先；原始的接口派生和手动实现仅简写提及，并附上 API 深入解读的链接以获取完整细节。

| 模式 | 最简单（Quick Start） | 详细（API Deep Dive） |
|---|---|---|
| 配置 | `services.AddX(opts => opts.Key = val)` | 自定义 `IConfigureOptions<X>` |
| 中间件 | `app.UseX()` 扩展方法 | 自定义 `IMiddleware` 实现 |
| 路由 | `[Route]` + `[HttpGet]` 属性 | 自定义 `IControllerActivator` |
| 日志 | `ILogger<T>` DI 注入 | 自定义 `ILoggerProvider` |
| **命令/属性** | `[VeloxCommand]` / `[VeloxProperty]` 特性 | 手动实现 `IVeloxCommand` / `INotifyPropertyChanged` |

### 示例

假设要记录一个 .NET 后台服务的 Quick Start：

```markdown
### 添加后台服务

1. 使用扩展方法注册后台服务（顶层 API）：
```csharp
builder.Services.AddHostedService<DataSyncService>();
```

2. 创建继承 `BackgroundService` 的类：
```csharp
public class DataSyncService : BackgroundService
{
    private readonly ILogger<DataSyncService> _logger;

    public DataSyncService(ILogger<DataSyncService> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            _logger.LogInformation("同步数据中...");
            await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
        }
    }
}
```
```

**反模式——Quick Start 不应这样写：** 先展示 `IHostedService` 接口派生和手动 `Task` 管理。注册扩展方法和 `BackgroundService` 基类是最高层的 API，应属于 Quick Start。直接实现 `IHostedService` 属于 API 深入解读。

**Quick Start 关键原则：** 如果存在特性（Attribute）就用特性，如果存在 Fluent API 就用 Fluent API，如果存在基类就继承基类。手动 `interface` 实现留给 API 章节。

### 格式化要求

- 每个步骤用代码块展示完整可运行的代码
- 代码前有简短说明（1-3 句）
- **优先采纳最上层 API** — 特性优于接口、Fluent API 优于手动、扩展方法优于派生
- 底层或手动实现模式（如直接实现接口）应**简写标注"详见 API 深入解读"**，不在 Quick Start 中展开
- 高级模式标注「详见 API 深入解读」
- 输出位置：`content/{lang}/{category}/0_快速入门/` — 外层目录下按具体功能创建子页面

```
# 示例：分类组织，1_核心 包含 工作流、MVVM、过渡动画 三个功能
content/zh/1_核心/0_快速入门/
├── index.md                    ← 概览
├── 0_工作流/                   ← 功能子页
│   └── index.md
├── 1_MVVM/
│   └── index.md
└── 2_过渡动画/
    └── index.md
```

## 写入后操作

编写快速入门内容后：

- [ ] **重新生成导航索引** — 运行树生成脚本（如 `python gen_tree.py`）重建 tree.json
- [ ] **构建项目** — 运行 `dotnet build` 验证新内容正确嵌入
