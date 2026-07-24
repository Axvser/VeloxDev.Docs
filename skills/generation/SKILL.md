# Generation — Automated Wiki Content Generation

> **Sub-skill.** Load only when the user asks to generate Wiki content automatically from data or code.

Automatically produces Wiki pages from external data sources: C# APIs, Git history, JSON/CSV glossaries, and config schemas.

## When to Load

- "Generate API reference"
- "Create changelog from Git"
- "Build glossary from data file"
- "Generate configuration reference"
- "Auto-generate documentation from source"

## Generation Modes

| Mode | Input | Output |
|---|---|---|
| API Reference | C# public API + XML doc comments | Parameter tables + return values + examples |
| Changelog | Git commit history between tags | Version release notes Wiki page |
| Glossary | Structured JSON/CSV data | Alphabetically sorted glossary |
| Configuration Reference | Config files / schema docs | Configuration item description table |
