# Constraint Loading

## Responsibility

After determining the tech stack, load the corresponding language's documentation conventions. This skill is a dispatcher; specific constraints are defined in nested sub-skills.

## Dispatch Logic

Based on the tech analysis result, load the corresponding language constraint sub-skill:

| Detection Result | Load Sub-skill |
|---|---|
| .NET (C# / VB / F#) | `lang-constraints/dotnet/SKILL.md` |
| Rust | `lang-constraints/rust/SKILL.md` |
| TypeScript / JavaScript | `lang-constraints/typescript/SKILL.md` |
| Python | `lang-constraints/python/SKILL.md` |
| Go | `lang-constraints/go/SKILL.md` |
| C / C++ | `lang-constraints/c-cpp/SKILL.md` |
| Java | `lang-constraints/java/SKILL.md` |
| Unrecognized | Use generic documentation conventions (no sub-skill needed) |

## Example

```
# Assuming tech-analysis detected .slnx and .csproj files
→ Load skills/lang-constraints/dotnet/SKILL.md
  This constraint guides the Agent to use XML doc comments, document DI lifetimes, etc.
```

## Output

Merge the loaded constraint rules into the Agent's working memory. All subsequent documentation steps automatically comply with these rules.
