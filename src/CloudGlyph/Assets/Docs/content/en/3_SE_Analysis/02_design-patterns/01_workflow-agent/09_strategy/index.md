# Workflow Agent — Design Patterns — Strategy

`WorkflowToolCategory` flags let the host shrink the tool surface (lower token cost, better selection accuracy). `WithSelectionHandler` / `WithConfirmationHandler` provide the host's interaction strategy — the toolkit only registers `RequestSelection`/`RequestConfirmation` when a handler exists AND safety level > 0.

> Source: `WorkflowToolCategory.cs`; `WorkflowAgentToolkit.cs` lines 142-149.
