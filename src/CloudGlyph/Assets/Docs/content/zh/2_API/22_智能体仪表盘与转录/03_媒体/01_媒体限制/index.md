# 限制与转码

`AgentMediaOptions` 决定哪些负载可以传输，以及不适配时如何处理。库刻意不携带媒体编解码器：一个带原生图片、音频或视频依赖的平台中立包会把它们强加给每个消费者。

## 枚举

### AgentMediaKind

| 成员 | 含义 |
|---|---|
| `Unknown` | 未识别。 |
| `Image` | 图片。 |
| `Audio` | 音频。 |
| `Video` | 视频。 |
| `Document` | 文档（PDF、RTF、Office）。 |
| `Text` | 文本。 |
| `Binary` | 任意二进制；选择性加入。 |

### AgentMediaFormat

`Unknown`、`Png`、`Jpeg`、`Webp`、`Gif`、`Bmp`、`Tiff`、`Avif`、`Heic`、`Svg`、`Mp3`、`Wav`、`Flac`、`Ogg`、`Aac`、`M4a`、`Mp4`、`Webm`、`Mkv`、`Avi`、`Mpeg`、`QuickTime`、`Flv`、`Pdf`、`Zip`、`Rtf`、`PlainText`、`Html`、`Json`、`Xml`、`Csv`。

## 类：AgentMediaOptions

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `CreateDefault` | `static AgentMediaOptions CreateDefault()` | 一份新的内置默认。 |
| `CreateVisionDefault` | `static AgentMediaOptions CreateVisionDefault()` | 按视觉成本设定的默认：图片 1280×720。配合转码器，否则更大帧会被拒绝。 |
| `AllowedKinds` | `ISet<AgentMediaKind>` | 允许发送的种类。`Binary` 需选择性加入。 |
| `AllowedMediaTypes` | `ISet<string>?` | 允许发送的确切媒体类型。`null` 表示某允许种类的所有类型。 |
| `MaxBytes` | `long` | 未在 `MaxBytesByKind` 中列出种类的兜底字节上限。 |
| `MaxBytesByKind` | `IDictionary<AgentMediaKind, long>` | 逐种类上限。 |
| `MaxWidth` / `MaxHeight` | `int` | 接受的最大图片尺寸。默认 4096。 |
| `StrictMediaType` | `bool` | 设置时，与字节矛盾的声明类型被拒绝而非纠正。 |
| `AllowAnimated` | `bool` | 是否接受动画 GIF/WebP。默认 `false`。 |
| `Transcoder` | `IAgentMediaTranscoder?` | 用于转换或缩小的编解码器。没有它时此类负载以 `TranscoderRequired` 拒绝。 |
| `TranscodeFormat` | `AgentMediaFormat` | 转码器应产出的图片容器。默认 `Png`。 |
| `TranscodeMediaType` | `string?` | 非图片负载的目标类型；`null` 表示按源类型重编码。 |
| `TranscodeQuality` | `int` | 有损输出质量提示，1–100。默认 85。 |

## 枚举：AgentMediaError

`Empty`、`UnknownFormat`、`UnsupportedKind`、`UnsupportedMediaType`、`MediaTypeMismatch`、`TooLarge`、`TooWide`、`Animated`、`InvalidDataUri`、`InvalidUrl`、`TranscoderRequired`、`TranscodeFailed`、`InvalidTranscoderResult`。

## 类：AgentMediaException

被拒绝的负载，带调用方可分支的错误。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `AgentMediaException(AgentMediaError error, string message, Exception? innerException = null)` | 创建异常。 |
| `Error` | `AgentMediaError Error { get; }` | 出了什么问题。 |

调用方无需解析消息即可区分「太大」与「不是图片」，这正是纯文本回退所需要的。

## 转码接缝

### 枚举：AgentMediaTranscodeReason

`UnsupportedKind`、`UnsupportedMediaType`、`UnrecognizedFormat`、`OversizeBytes`、`OversizeDimensions`、`Animated`。

### 类：AgentMediaTranscodeRequest

| 成员 | 类型 | 说明 |
|---|---|---|
| `Reason` | `AgentMediaTranscodeReason` | 请求转码的原因。 |
| `TargetKind` | `AgentMediaKind` | 结果应具有的种类。 |
| `TargetMediaType` | `string` | 目标媒体类型。 |
| `MaxWidth` / `MaxHeight` | `int` | 图片边界。 |
| `MaxBytes` | `long` | 字节目标；`0` 表示无。 |
| `Quality` | `int` | 质量提示，1–100。 |

### 接口：IAgentMediaTranscoder

| 成员 | 签名 | 说明 |
|---|---|---|
| `TranscodeAsync` | `Task<AgentMedia> TranscodeAsync(AgentMedia source, AgentMediaTranscodeRequest request, CancellationToken cancellationToken = default)` | 转换或缩小负载。结果由调用方再次校验；原样返回源不是退出方式。 |

`DelegateAgentMediaTranscoder(Func<AgentMedia, AgentMediaTranscodeRequest, CancellationToken, Task<AgentMedia>> transcode)` 把 lambda 包装为转码器。

### 接口：IAgentMediaContent

用户消息可作为媒体携带的东西：字节（`AgentMedia`）或远程引用（`AgentMediaReference`）。消息构建器接受它而非仅字节，因为能获取 URL 的 provider 不需要宿主先下载。

## 相关

- [AgentMedia 与消息构建](../00_媒体负载/index.md) —— 这些限制作用的负载。
- [带媒体运行](../02_媒体运行/index.md) —— 运行辅助。
