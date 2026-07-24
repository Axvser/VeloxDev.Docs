# FAQ — Frequently Asked Questions & Troubleshooting

> **Sub-skill.** Load only when the user asks to write an FAQ or troubleshooting guide.

## When to Load

- "Compile an FAQ"
- "Write a troubleshooting guide"
- "Troubleshooting documentation"
- "Extract FAQ from Issues"

## Information Sources

- GitHub Issues (filter by labels: `question`, `bug`, `help wanted`)
- Stack Overflow tagged pages
- Discord / Slack chat history for frequently asked questions
- Existing PR discussions and review comments

## Document Structure

```
FAQ /
├── index.md                    ← Table of contents + category index
├── 01_Installation/            ← Installation issues
├── 02_Configuration/           ← Configuration issues
├── 03_Usage/                   ← Usage questions
└── 04_Troubleshooting/         ← Errors and troubleshooting
```

## Entry Format

```markdown
## Q: Question title?

**A:** Answer text

<!-- If there is a code example -->
```lang
code
```

<!-- If there is a related Issue -->
> Reference: [Issue #123](link)
```
