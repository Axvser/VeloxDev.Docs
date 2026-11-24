# AgentMedia 与消息构建

`AgentMedia` 是框架内容块之前的一步：它嗅探容器、分类种类、规范化媒体类型、读取图片尺寸并应用调用方限制。字节胜过声明的类型。

## 类：AgentMedia

`VeloxDev.AI.AgentMedia : IAgentMediaContent`

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Bytes` | `ReadOnlyMemory<byte>` | 原始容器字节。 |
| `Format` | `AgentMediaFormat` | 识别出的容器，通用二进制为 `Unknown`。 |
| `Kind` | `AgentMediaKind` | 大类。 |
| `MediaType` | `string` | 取自字节的规范类型，无魔数时取自声明。 |
| `Name` | `string?` | 显示名。 |
| `DeclaredMediaType` | `string?` | 调用方声明规范化后的结果；保留以便严格检查报告矛盾。 |
| `Width` / `Height` | `int?` | 从图片头读取的尺寸。 |
| `ByteCount` | `int` | 原始字节数；不含 base64 膨胀。 |
| `IsAnimated` | `bool` | 头部是否表明是动画 GIF 或 WebP。 |
| `FromBytes` | `static AgentMedia FromBytes(ReadOnlyMemory<byte> bytes, string? mediaType = null, string? name = null)` | 从字节创建。字节为空或声称图片而字节不是图片时抛异常。 |
| `FromFile` | `static AgentMedia FromFile(string path, string? mediaType = null)` | 读取文件；扩展名只是提示。 |
| `FromFileAsync` | `static Task<AgentMedia> FromFileAsync(string path, string? mediaType = null, CancellationToken cancellationToken = default)` | 非阻塞读取。 |
| `FromStream` | `static AgentMedia FromStream(Stream stream, string? mediaType = null, string? name = null)` | 读取流并保持其打开。 |
| `FromStreamAsync` | `static Task<AgentMedia> FromStreamAsync(Stream stream, string? mediaType = null, string? name = null, CancellationToken cancellationToken = default)` | 非阻塞读取并保持流打开。 |
| `FromDataUri` | `static AgentMedia FromDataUri(string dataUri, string? name = null)` | 解析 base64 或百分号编码的 `data:` URI。格式错误时抛异常。 |
| `ToBase64String()` | `string ToBase64String()` | 原始字节的 base64。 |
| `ToDataUri()` | `string ToDataUri()` | 规范的 `data:` URI。 |
| `ToDataContent()` | `DataContent ToDataContent()` | 框架的 `DataContent`。 |
| `ToTextContent()` | `TextContent ToTextContent()` | 把文本内联为文本而非数据文件；非图片/音频/PDF 的数据块到达 OpenAI 兼容模型时会变成空回合。 |
| `ToContent()` | `AIContent ToContent()` | 此负载的内容块。 |
| `Normalize(AgentMediaOptions? options = null)` | `AgentMedia Normalize(...)` | 校验而不转换。需要转码时抛异常。 |
| `NormalizeAsync(AgentMediaOptions? options = null, CancellationToken cancellationToken = default)` | `Task<AgentMedia> NormalizeAsync(...)` | 校验并通过转码器转换或缩小。 |
| `ToString()` | `string ToString()` | 简短描述。 |

选择器声称 `image/jpeg` 但字节是 PNG 时会被纠正而非拒绝。声称图片却没有图片魔数会在构造时被拒，因为 provider 无法分类它。

## 类：AgentAttachment

用户回合除文本外携带的内容——显示记录，不是字节。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| 构造函数 | `AgentAttachment(string? name, string mediaType, long? byteCount = null, string? uri = null)` | 创建记录。 |
| `Name` | `string?` | 显示名。 |
| `MediaType` | `string` | 规范媒体类型。 |
| `Kind` | `AgentMediaKind` | 由媒体类型派生的大类。 |
| `ByteCount` | `long?` | 原始负载大小，已知时。 |
| `Uri` | `string?` | 远程位置，用于 URL 引用。 |
| `Describe()` | `string Describe()` | 一行描述，如 `frame.png (image/png, 79 KB)`。 |

## 类：AgentMediaReference

provider 可获取的远程负载，此处不下载。

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Uri` | `Uri` | 绝对 HTTP(S) 位置。 |
| `Kind` | `AgentMediaKind` | 大类。 |
| `MediaType` | `string` | 媒体类型。 |
| `Name` | `string?` | 显示名。 |
| `FromUrl` | `static AgentMediaReference FromUrl(string url, string? mediaType = null, string? name = null)` | 创建引用。URL 非 HTTP(S) 或类型无法确定时抛异常。 |
| `ToContent()` | `AIContent ToContent()` | 内容块。 |

`file:` URI 被拒绝：provider 无法读取调用方磁盘。此处不下载字节，因此尺寸、时长与大小无法检查。

## 类：AgentMessage

构建携带多模态输入的用户消息。文本块在前，媒体按调用方顺序跟随。

| 方法 | 返回 | 说明 |
|---|---|---|
| `User(string? text, params IAgentMediaContent[] media)` | `ChatMessage` | 从文本与已校验媒体构建。两者都空时抛异常。 |
| `User(string? text, IEnumerable<IAgentMediaContent>? media)` | `ChatMessage` | 可枚举重载。 |
| `FromContents(params AIContent[] contents)` | `ChatMessage` | 从原始块构建，不校验。未提供内容时抛异常。 |
| `CreateUser(string? text, IEnumerable<AgentMedia>? media, AgentMediaOptions? options = null)` | `ChatMessage` | 同步校验并构建。 |
| `CreateUserAsync(string? text, IEnumerable<AgentMedia>? media, AgentMediaOptions? options = null, CancellationToken cancellationToken = default)` | `Task<ChatMessage>` | 校验、转换或缩小后构建。 |

## 示例

```csharp
using VeloxDev.AI;

var image = await AgentMedia.FromFileAsync("preview/frame.png");
var message = await AgentMessage.CreateUserAsync("Check the frame.", new[] { image });
```

## 相关

- [限制与转码](../01_媒体限制/index.md) —— `AgentMediaOptions` 与编解码接缝。
- [带媒体运行](../02_媒体运行/index.md) —— 一次调用的运行辅助。
