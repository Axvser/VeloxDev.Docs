# AgentMedia and message building

`AgentMedia` is the step before the framework's content blocks: it sniffs the container, classifies the kind, canonicalises the media type, reads image dimensions and applies the caller's limits. Bytes win over a declared type.

## Class: AgentMedia

`VeloxDev.AI.AgentMedia : IAgentMediaContent`

| Member | Type / Signature | Description |
|---|---|---|
| `Bytes` | `ReadOnlyMemory<byte>` | The raw container bytes. |
| `Format` | `AgentMediaFormat` | The recognised container, or `Unknown` for a generic blob. |
| `Kind` | `AgentMediaKind` | The broad class. |
| `MediaType` | `string` | The canonical type taken from the bytes, or from the declaration when there is no magic. |
| `Name` | `string?` | The display name. |
| `DeclaredMediaType` | `string?` | The caller's claim, canonicalised; kept so a strict check can report the contradiction. |
| `Width` / `Height` | `int?` | Dimensions read from an image header. |
| `ByteCount` | `int` | Raw byte count; base64 expansion not included. |
| `IsAnimated` | `bool` | Whether the header says this is an animated GIF or WebP. |
| `FromBytes` | `static AgentMedia FromBytes(ReadOnlyMemory<byte> bytes, string? mediaType = null, string? name = null)` | Creates a payload from bytes. Throws when the bytes are empty or an image was claimed but the bytes are not one. |
| `FromFile` | `static AgentMedia FromFile(string path, string? mediaType = null)` | Reads a file; the extension is a hint only. |
| `FromFileAsync` | `static Task<AgentMedia> FromFileAsync(string path, string? mediaType = null, CancellationToken cancellationToken = default)` | The non-blocking read. |
| `FromStream` | `static AgentMedia FromStream(Stream stream, string? mediaType = null, string? name = null)` | Reads a stream, leaving it open. |
| `FromStreamAsync` | `static Task<AgentMedia> FromStreamAsync(Stream stream, string? mediaType = null, string? name = null, CancellationToken cancellationToken = default)` | The non-blocking read, leaving the stream open. |
| `FromDataUri` | `static AgentMedia FromDataUri(string dataUri, string? name = null)` | Parses a base64 or percent-encoded `data:` URI. Throws when malformed. |
| `ToBase64String()` | `string ToBase64String()` | The raw bytes as base64. |
| `ToDataUri()` | `string ToDataUri()` | The canonical `data:` URI. |
| `ToDataContent()` | `DataContent ToDataContent()` | The framework's `DataContent`. |
| `ToTextContent()` | `TextContent ToTextContent()` | Inlines text as text rather than a data file; a non-image/audio/PDF data block reaches an OpenAI-compatible model as an empty turn. |
| `ToContent()` | `AIContent ToContent()` | The content block for this payload. |
| `Normalize(AgentMediaOptions? options = null)` | `AgentMedia Normalize(...)` | Validates without converting. Throws when a transcode would be needed. |
| `NormalizeAsync(AgentMediaOptions? options = null, CancellationToken cancellationToken = default)` | `Task<AgentMedia> NormalizeAsync(...)` | Validates and converts or shrinks through the transcoder. |
| `ToString()` | `string ToString()` | A short description. |

A picker that says `image/jpeg` over PNG bytes is corrected, not rejected. A claim of an image with no image magic is rejected at construction, because a provider cannot classify it.

## Class: AgentAttachment

What a user turn carried besides text — the display record, not the bytes.

| Member | Type / Signature | Description |
|---|---|---|
| Constructor | `AgentAttachment(string? name, string mediaType, long? byteCount = null, string? uri = null)` | Creates the record. |
| `Name` | `string?` | Display name. |
| `MediaType` | `string` | Canonical media type. |
| `Kind` | `AgentMediaKind` | Broad class derived from the media type. |
| `ByteCount` | `long?` | Raw payload size, when known. |
| `Uri` | `string?` | Remote location, for a URL reference. |
| `Describe()` | `string Describe()` | One-line description, e.g. `frame.png (image/png, 79 KB)`. |

## Class: AgentMediaReference

A remote payload the provider can fetch, without downloading it here.

| Member | Type / Signature | Description |
|---|---|---|
| `Uri` | `Uri` | The absolute HTTP(S) location. |
| `Kind` | `AgentMediaKind` | Broad class. |
| `MediaType` | `string` | Media type. |
| `Name` | `string?` | Display name. |
| `FromUrl` | `static AgentMediaReference FromUrl(string url, string? mediaType = null, string? name = null)` | Creates a reference. Throws when the URL is not HTTP(S) or the type cannot be established. |
| `ToContent()` | `AIContent ToContent()` | The content block. |

A `file:` URI is rejected: a provider cannot read the caller's disk. No bytes are downloaded, so dimensions, duration and size cannot be checked here.

## Class: AgentMessage

Builds the user message that carries multimodal input. The text block comes first and the media follows in the caller's order.

| Method | Returns | Description |
|---|---|---|
| `User(string? text, params IAgentMediaContent[] media)` | `ChatMessage` | From text and already-validated media. Throws when both are empty. |
| `User(string? text, IEnumerable<IAgentMediaContent>? media)` | `ChatMessage` | The enumerable overload. |
| `FromContents(params AIContent[] contents)` | `ChatMessage` | From raw blocks, with no validation. Throws when none were supplied. |
| `CreateUser(string? text, IEnumerable<AgentMedia>? media, AgentMediaOptions? options = null)` | `ChatMessage` | Validates synchronously and builds the message. |
| `CreateUserAsync(string? text, IEnumerable<AgentMedia>? media, AgentMediaOptions? options = null, CancellationToken cancellationToken = default)` | `Task<ChatMessage>` | Validates, converts or shrinks, then builds. |

## Example

```csharp
using VeloxDev.AI;

var image = await AgentMedia.FromFileAsync("preview/frame.png");
var message = await AgentMessage.CreateUserAsync("Check the frame.", new[] { image });
```

## Related

- [Limits and transcoding](../01_media-options/index.md) — `AgentMediaOptions` and the codec seam.
- [Running with media](../02_media-run/index.md) — the one-call run helpers.
