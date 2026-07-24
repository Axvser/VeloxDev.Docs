# ADR — Architecture Decision Records & Meeting Notes

> **Sub-skill.** Load only when the user asks to write Architecture Decision Records or meeting notes.

## When to Load

- "Record an architecture decision"
- "Write an ADR"
- "Organize meeting notes"
- "Decision log"

## ADR Template

```markdown
# ADR-{Number}: {Title}

- **Status:** [Proposed | Accepted | Deprecated | Superseded]
- **Date:** {YYYY-MM-DD}
- **Author:** {Name}

## Context

Why is this decision needed? What problem are we facing?

## Options

### Option A: {Name}
- Pros: ...
- Cons: ...
- Cost: ...

### Option B: {Name}
- Pros: ...
- Cons: ...
- Cost: ...

## Decision

Which option was chosen and why?

## Consequences

Positive and negative impacts of this decision, follow-up actions.

## References

- Related Issue/PR links
- Related ADR links
```

## Output Location

`content/{lang}/{Project}/adr/ADR_{Number}.md`
