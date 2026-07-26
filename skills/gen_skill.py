"""
gen_skill.py

Collects Meta.md from each sub-skill directory, parses [#Tag] markers,
groups skills by [#group], and injects the generated Sub-Skill Directory
Index into Base.md to produce the final SKILL.md.

Supports multiple languages via --lang parameter.

Usage:
    python skills/gen_skill.py                  # default: en
    python skills/gen_skill.py --lang zh        # Chinese
    python skills/gen_skill.py --lang en        # English

Or from any working directory — the script auto-detects its location relative
to the skills/ folder.
"""

import argparse
import os
import re
import sys
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────

# Script lives in skills/ — use that as the root
SKILLS_ROOT = os.path.abspath(os.path.dirname(__file__))

def get_paths(lang: str) -> tuple[str, str]:
    """Return (template_path, skill_output_path) for the given language.

    Template is read from {lang}/TEMPLATE.md.
    Output is written to skills/SKILL.md (the root entry point).
    """
    template_path = os.path.join(SKILLS_ROOT, lang, "TEMPLATE.md")
    skill_output = os.path.join(SKILLS_ROOT, "SKILL.md")
    return template_path, skill_output

# Directories to skip when scanning for sub-skills
_SKIP_DIRS = {"__pycache__", ".git", ".github"}

# Regex to detect a [#Tag] at the start of a line
_TAG_RE = re.compile(r"^\[#(\w+)\](?:\s+(.*))?$")


# ── Meta.md Parser ────────────────────────────────────────────────────

def parse_meta(path: str) -> dict[str, str]:
    """Parse a Meta.md file and return a dict of {tag: content}.

    Tags are identified by ``[#tagname]`` at the start of a line.
    Content continues until the next ``[#tagname]`` or EOF.
    Leading/trailing blank lines are stripped from each tag's content.
    """
    result: dict[str, str] = {}
    current_tag: Optional[str] = None
    current_lines: list[str] = []

    def flush():
        if current_tag is not None:
            text = "\n".join(current_lines).strip()
            if text:
                result[current_tag] = text

    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                m = _TAG_RE.match(line)
                if m:
                    flush()
                    current_tag = m.group(1)
                    trailing = m.group(2)
                    current_lines = [trailing] if trailing else []
                elif current_tag is not None:
                    current_lines.append(line)
        flush()
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[gen_skill] WARNING: Error reading {path}: {e}", file=sys.stderr)

    return result


# ── Table Generator ───────────────────────────────────────────────────

def escape_pipe(text: str) -> str:
    """Escape pipe characters for markdown table cells."""
    return text.replace("|", "\\|")


# Preferred group display order (canonical: Chinese tags from Meta.md)
_GROUP_ORDER = [
    "基础设置",
    "约束加载",
    "内容编写",
    "质量保障",
]

# Language-specific display configs for the generated index
_LANG_CONFIG = {
    "en": {
        "intro": (
            "Sub-skills are organized into independent directories by scenario. "
            "The Agent should only load a sub-skill's `SKILL.md` when the user's request "
            "matches the corresponding scenario \u2014 do not pre-load."
        ),
        "columns": ["Path", "Scenario", "Trigger Keywords"],
        "groups": {
            "基础设置": "Foundation Setup",
            "约束加载": "Constraint Loading",
            "内容编写": "Content Writing",
            "质量保障": "Quality Assurance",
        },
    },
    "zh": {
        "intro": (
            "子技能按场景组织到独立目录中。Agent 仅在用户请求匹配对应场景时加载子技能的 "
            "`SKILL.md`，切勿预加载。"
        ),
        "columns": ["路径", "场景", "触发关键词"],
        "groups": {
            "基础设置": "基础设置",
            "约束加载": "约束加载",
            "内容编写": "内容编写",
            "质量保障": "质量保障",
        },
    },
}


def _get_lang_text(lang: str, key: str, group_name: str | None = None) -> str:
    """Get language-specific display text.

    If *group_name* is given, looks up the group display name.
    Otherwise looks up *key* (e.g. 'intro', 'columns').
    """
    cfg = _LANG_CONFIG.get(lang) or _LANG_CONFIG["en"]
    if group_name is not None:
        return cfg["groups"].get(group_name, group_name)
    return cfg.get(key, "")  # type: ignore[return-value]


def _get_lang_columns(lang: str) -> list[str]:
    """Get the column header strings for the given language."""
    return _LANG_CONFIG.get(lang, _LANG_CONFIG["en"])["columns"]


def _group_sort_key(group: str) -> int:
    try:
        return _GROUP_ORDER.index(group)
    except ValueError:
        return len(_GROUP_ORDER)


def generate_skill_index(skills: list[dict], lang: str = "en") -> str:
    """Generate the full Sub-Skill Directory Index markdown section.

    *skills* is a list of dicts with keys: group, route, description, workflow, phase, rules.
    Skills are grouped by [group] in the order defined by _GROUP_ORDER.
    *lang* controls the display language (intro text, column headers, group names).
    Returns the markdown string (without the surrounding --- separators).
    """
    # Group by [group]
    groups: dict[str, list[dict]] = {}
    for s in skills:
        group = s.get("group", "Uncategorized")
        groups.setdefault(group, []).append(s)

    # Sort groups by preferred order
    sorted_groups = sorted(groups.items(), key=lambda kv: _group_sort_key(kv[0]))

    # Sort skills within each group by route
    for group_name in groups:
        groups[group_name].sort(key=lambda s: s.get("route", ""))

    columns = _get_lang_columns(lang)
    parts: list[str] = []
    parts.append(_get_lang_text(lang, "intro"))
    parts.append("")

    for group_name, items in sorted_groups:
        display_group = _get_lang_text(lang, "groups", group_name)
        parts.append(f"### {display_group}")
        parts.append("")
        parts.append(f"| {columns[0]} | {columns[1]} | {columns[2]} |")
        parts.append("|---|---|---|")

        for s in items:
            route = s.get("route", "")
            description = s.get("description", "")
            workflow = s.get("workflow", "")
            phase = s.get("phase", "")
            depth = s.get("depth", 0)

            # Indent route by nesting depth
            indent = "  " * depth
            display_route = route
            if depth > 0:
                display_route = f"{indent}{route}"

            # Combine description + phase info
            scenario = description
            if phase:
                scenario = f"{description} — {phase}"

            # Trigger keywords from workflow lines
            triggers = _format_workflow(workflow)

            parts.append(
                f"| `{escape_pipe(display_route)}`"
                f" | {escape_pipe(scenario)}"
                f" | {escape_pipe(triggers)} |"
            )

        parts.append("")

    return "\n".join(parts).rstrip("\n") + "\n"


def generate_flat_table(skills: list[dict]) -> str:
    """Generate a standalone mapping table Markdown file.

    Produces a single flat table with columns: 分组, 路径, 场景, 触发关键词.
    """
    # Group and sort same as generate_skill_index
    groups: dict[str, list[dict]] = {}
    for s in skills:
        group = s.get("group", "Uncategorized")
        groups.setdefault(group, []).append(s)

    sorted_groups = sorted(groups.items(), key=lambda kv: _group_sort_key(kv[0]))

    for group_name in groups:
        groups[group_name].sort(key=lambda s: s.get("route", ""))

    parts: list[str] = []
    parts.append("# 技能索引 — 对照表")
    parts.append("")
    parts.append("| 分组 | 路径 | 场景 | 触发关键词 |")
    parts.append("|---|---|---|---|")

    for group_name, items in sorted_groups:
        first = True
        for s in items:
            route = s.get("route", "")
            description = s.get("description", "")
            workflow = s.get("workflow", "")
            phase = s.get("phase", "")
            depth = s.get("depth", 0)

            indent = "  " * depth
            display_route = route
            if depth > 0:
                display_route = f"{indent}{route}"

            scenario = description
            if phase:
                scenario = f"{description} — {phase}"

            triggers = _format_workflow(workflow)

            cell_group = group_name if first else ""
            parts.append(
                f"| {escape_pipe(cell_group)}"
                f" | `{escape_pipe(display_route)}`"
                f" | {escape_pipe(scenario)}"
                f" | {escape_pipe(triggers)} |"
            )
            first = False

    parts.append("")
    return "\n".join(parts) + "\n"


def _format_workflow(workflow_text: str) -> str:
    """Format workflow trigger keywords into a comma-separated string.

    Handles various list formats:
    - "- \"keyword\"" (markdown list with quoted strings)
    - "- keyword" (plain markdown list)
    - "keyword1, keyword2" (comma-separated)
    """
    if not workflow_text:
        return ""

    lines = workflow_text.strip().split("\n")
    keywords: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove leading "- " or "* " (markdown list markers)
        if line.startswith("- "):
            line = line[2:]
        elif line.startswith("* "):
            line = line[2:]
        # Strip surrounding quotes
        line = line.strip('"').strip("'")
        if line:
            keywords.append(line)

    return ", ".join(keywords)


# ── Main ──────────────────────────────────────────────────────────────

def _collect_skills_recursive(
    search_root: str,
    skills: list[dict],
    lang: str,
    lang_root: str,
    parent_meta: Optional[dict] = None,
    depth: int = 0,
) -> None:
    """Recursively walk *search_root* subdirectories and collect Meta.md data.

    *parent_meta* is the parsed Meta.md of the parent directory (used for
    group inheritance). *depth* tracks nesting level for indented display.
    *lang* is the language code used to prefix routes (e.g. 'en', 'zh').
    """
    for entry in sorted(os.listdir(search_root)):
        sub_path = os.path.join(search_root, entry)
        if not os.path.isdir(sub_path):
            continue
        if entry.startswith(".") or entry in _SKIP_DIRS:
            continue

        meta_path = os.path.join(sub_path, "Meta.md")
        meta = parse_meta(meta_path) if os.path.isfile(meta_path) else {}

        # Build skill entry if Meta.md exists and has at minimum a description
        if meta:
            # Inherit group from parent if not explicitly set
            group = meta.get("group") or (parent_meta.get("group") if parent_meta else None) or "Uncategorized"

            # Auto-generate route relative to SKILLS_ROOT if not explicitly set
            route = meta.get("route")
            if not route:
                rel = os.path.relpath(sub_path, lang_root).replace("\\", "/")
                route = f"skills/{lang}/{rel}/SKILL.md"
                meta["route"] = route

            skill = {
                "group": group,
                "route": route,
                "description": meta.get("description", ""),
                "workflow": meta.get("hook", "") or meta.get("workflow", ""),
                "rules": meta.get("rules", ""),
                "phase": meta.get("phase", ""),
                "depth": depth,
            }
            skills.append(skill)
            print(
                f"[gen_skill] Collected: {'  ' * depth}{os.path.relpath(sub_path, lang_root)}"
                f" → group={group} (depth={depth})"
            )

        # Recurse into this subdirectory (pass current meta for group inheritance)
        _collect_skills_recursive(sub_path, skills, lang, lang_root, meta if meta else parent_meta, depth + 1)


def collect_skills(lang: str) -> list[dict]:
    """Walk the language-specific subdirectory, collect Meta.md data.

    Scans SKILLS_ROOT/{lang}/ for sub-skill directories with Meta.md files.
    """
    lang_root = os.path.join(SKILLS_ROOT, lang)
    skills: list[dict] = []
    _collect_skills_recursive(lang_root, skills, lang, lang_root, parent_meta=None, depth=0)
    return skills


def assemble_skill_md(skills: list[dict], lang: str) -> str:
    """Read TEMPLATE.md for the given language, inject the generated skill index, return full content."""
    template_path, _ = get_paths(lang)
    if not os.path.isfile(template_path):
        print(f"[gen_skill] ERROR: TEMPLATE.md not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    index_md = generate_skill_index(skills, lang=lang)
    placeholder = "<!-- SKILL_INDEX -->"
    if placeholder not in template_content:
        print(
            f"[gen_skill] ERROR: Placeholder '{placeholder}' not found in TEMPLATE.md",
            file=sys.stderr,
        )
        sys.exit(1)

    return template_content.replace(placeholder, index_md, 1)


def main():
    parser = argparse.ArgumentParser(description="Generate SKILL.md from Meta.md files")
    parser.add_argument("--lang", default="en", help="Language code (e.g. 'en', 'zh'). Default: en")
    args = parser.parse_args()
    lang = args.lang

    template_path, skill_output_path = get_paths(lang)

    print(f"[gen_skill] Language: {lang}")
    print(f"[gen_skill] Template: {template_path}")
    print(f"[gen_skill] Output: {skill_output_path}")
    print("[gen_skill] Scanning skills/ for Meta.md files...")
    skills = collect_skills(lang)

    if not skills:
        print("[gen_skill] No sub-skills with Meta.md found — SKILL.md will have an empty index.")
    else:
        print(f"[gen_skill] Found {len(skills)} sub-skill(s) with Meta.md")

    # Generate SKILL.md (_template.md + skill index)
    full_content = assemble_skill_md(skills, lang)

    with open(skill_output_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"[gen_skill] Generated: {skill_output_path}")
    print("[gen_skill] Done.")


if __name__ == "__main__":
    main()
