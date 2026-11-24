# Limits and transcoding

`AgentMediaOptions` decides which payloads may travel and what to do when one does not fit. The library carries no media codec on purpose: a platform-neutral package with native image, audio or video dependencies would force them on every consumer.

## Enums

### AgentMediaKind

| Member | Meaning |
|---|---|
| `Unknown` | Unrecognised. |
| `Image` | Image. |
| `Audio` | Audio. |
| `Video` | Video. |
| `Document` | Document (PDF, RTF, Office). |
| `Text` | Text. |
| `Binary` | Arbitrary binary; opt-in. |

### AgentMediaFormat

`Unknown`, `Png`, `Jpeg`, `Webp`, `Gif`, `Bmp`, `Tiff`, `Avif`, `Heic`, `Svg`, `Mp3`, `Wav`, `Flac`, `Ogg`, `Aac`, `M4a`, `Mp4`, `Webm`, `Mkv`, `Avi`, `Mpeg`, `QuickTime`, `Flv`, `Pdf`, `Zip`, `Rtf`, `PlainText`, `Html`, `Json`, `Xml`, `Csv`.

## Class: AgentMediaOptions

| Member | Type / Signature | Description |
|---|---|---|
| `CreateDefault` | `static AgentMediaOptions CreateDefault()` | A fresh set of the shipped defaults. |
| `CreateVisionDefault` | `static AgentMediaOptions CreateVisionDefault()` | Defaults sized for vision cost: 1280×720 for images. Pair with a transcoder, or a larger frame is rejected. |
| `AllowedKinds` | `ISet<AgentMediaKind>` | Kinds that may be sent. `Binary` is opt-in. |
| `AllowedMediaTypes` | `ISet<string>?` | Exact media types that may be sent. `null` means every type of an allowed kind. |
| `MaxBytes` | `long` | Fallback byte limit for a kind without an entry in `MaxBytesByKind`. |
| `MaxBytesByKind` | `IDictionary<AgentMediaKind, long>` | Per-kind limits. |
| `MaxWidth` / `MaxHeight` | `int` | Largest accepted image dimension. Default 4096. |
| `StrictMediaType` | `bool` | When set, a declared type that contradicts the bytes is rejected instead of corrected. |
| `AllowAnimated` | `bool` | Whether an animated GIF/WebP is accepted. Default `false`. |
| `Transcoder` | `IAgentMediaTranscoder?` | The codec used to convert or shrink. Without one, such a payload is rejected with `TranscoderRequired`. |
| `TranscodeFormat` | `AgentMediaFormat` | Image container a transcoder should produce. Default `Png`. |
| `TranscodeMediaType` | `string?` | Target type for a non-image payload; `null` re-encodes in the source type. |
| `TranscodeQuality` | `int` | Quality hint for lossy output, 1–100. Default 85. |

## Enum: AgentMediaError

`Empty`, `UnknownFormat`, `UnsupportedKind`, `UnsupportedMediaType`, `MediaTypeMismatch`, `TooLarge`, `TooWide`, `Animated`, `InvalidDataUri`, `InvalidUrl`, `TranscoderRequired`, `TranscodeFailed`, `InvalidTranscoderResult`.

## Class: AgentMediaException

A rejected payload, with an error the caller can branch on.

| Member | Signature | Description |
|---|---|---|
| Constructor | `AgentMediaException(AgentMediaError error, string message, Exception? innerException = null)` | Creates the exception. |
| `Error` | `AgentMediaError Error { get; }` | What went wrong. |

The caller can tell "too large" from "not an image" without parsing the message, which is what a text-only fallback needs.

## Transcoding seam

### Enum: AgentMediaTranscodeReason

`UnsupportedKind`, `UnsupportedMediaType`, `UnrecognizedFormat`, `OversizeBytes`, `OversizeDimensions`, `Animated`.

### Class: AgentMediaTranscodeRequest

| Member | Type | Description |
|---|---|---|
| `Reason` | `AgentMediaTranscodeReason` | Why the transcode was requested. |
| `TargetKind` | `AgentMediaKind` | The kind the result should have. |
| `TargetMediaType` | `string` | The target media type. |
| `MaxWidth` / `MaxHeight` | `int` | Image bounds. |
| `MaxBytes` | `long` | Byte target; `0` means none. |
| `Quality` | `int` | Quality hint, 1–100. |

### Interface: IAgentMediaTranscoder

| Member | Signature | Description |
|---|---|---|
| `TranscodeAsync` | `Task<AgentMedia> TranscodeAsync(AgentMedia source, AgentMediaTranscodeRequest request, CancellationToken cancellationToken = default)` | Converts or shrinks a payload. The result is validated again by the caller; returning the source unchanged is not a way to opt out. |

`DelegateAgentMediaTranscoder(Func<AgentMedia, AgentMediaTranscodeRequest, CancellationToken, Task<AgentMedia>> transcode)` wraps a lambda as a transcoder.

### Interface: IAgentMediaContent

Something a user message can carry as media: bytes (`AgentMedia`) or a remote reference (`AgentMediaReference`). The message builder accepts this rather than only bytes because a provider that can fetch a URL need not have the host download it first.

## Related

- [AgentMedia and message building](../00_AgentMedia/index.md) — the payload these limits apply to.
- [Running with media](../02_media-run/index.md) — the run helpers.
