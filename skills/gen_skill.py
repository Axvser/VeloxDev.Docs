"""
gen_skill.py

Scans skills/{lang}/ for skill directories containing Meta.md,
parses [#pipeline] and [#description] tags, dynamically constructs
the workflow section, and inlines each skill's SKILL.md content
after its corresponding workflow step.

Supports multiple languages via --lang parameter.

Usage:
    python skills/gen_skill.py                  # default: en
    python skills/gen_skill.py --lang zh        # Chinese
    python skills/gen_skill.py --lang en        # English

Or from any working directory — the script auto-detects its location relative
to the skills/ folder.
"""

import argparse
import json
import os
import re
import sys
from typing import Optional

# Script lives in skills/ — use that as the root
SKILLS_ROOT = os.path.abspath(os.path.dirname(__file__))

WORKFLOW_PLACEHOLDER = "<!-- WORKFLOW -->"

_SKIP_DIRS = {"__pycache__", ".git", ".github"}

_TAG_RE = re.compile(r"^\[#(\w+)\](?:\s+(.*))?$")

_HEADING_RE = re.compile(r"^(#{1,6})\s")

# Indentation convention: code blocks MUST use spaces, never tabs.
TAB_WIDTH = 4


def expand_tabs(text: str, width: int = TAB_WIDTH) -> str:
    """Expand leading tab characters to *width* spaces.

    Enforces the indentation convention at assembly time so the generated
    SKILL.md never contains tab indentation, regardless of source files.
    Inline tabs (not at line start) are left untouched.
    """
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.lstrip("\t")
        n_tabs = len(line) - len(stripped)
        if n_tabs:
            line = " " * (n_tabs * width) + stripped
        out.append(line)
    return "\n".join(out)


def get_paths(lang: str) -> tuple[str, str]:
    template_path = os.path.join(SKILLS_ROOT, lang, "TEMPLATE.md")
    skill_output = os.path.join(SKILLS_ROOT, "SKILL.md")
    return template_path, skill_output


def parse_meta(path: str) -> dict[str, str]:
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


def demote_headings(text: str, levels: int = 1) -> str:
    if levels <= 0:
        return text

    lines = text.split("\n")
    result: list[str] = []
    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            prefix = m.group(1)
            rest = line[m.end() - 1:]
            result.append(f"{'#' * (len(prefix) + levels)}{rest}")
        else:
            result.append(line)
    return "\n".join(result)


def collect_skills(lang: str) -> list[dict]:
    lang_root = os.path.join(SKILLS_ROOT, lang)
    skills: list[dict] = []

    for entry in sorted(os.listdir(lang_root)):
        sub_path = os.path.join(lang_root, entry)
        if not os.path.isdir(sub_path):
            continue
        if entry.startswith(".") or entry in _SKIP_DIRS:
            continue

        meta_path = os.path.join(sub_path, "Meta.md")
        if not os.path.isfile(meta_path):
            continue

        meta = parse_meta(meta_path)
        pipeline = meta.get("pipeline", "")
        description = meta.get("description", "")

        if not pipeline:
            print(f"[gen_skill] WARNING: {entry}/Meta.md has no [#pipeline] - skipping", file=sys.stderr)
            continue

        skill_path = os.path.join(sub_path, "SKILL.md")
        if not os.path.isfile(skill_path):
            print(f"[gen_skill] WARNING: {entry}/SKILL.md not found - skipping", file=sys.stderr)
            continue

        skills.append({
            "pipeline": pipeline,
            "description": description,
            "sub_dir": entry,
            "skill_path": skill_path,
        })
        print(f"[gen_skill] Collected: {entry} -> pipeline={pipeline}")

    skills.sort(key=lambda s: int(s["pipeline"]))
    return skills


def parse_template_file(path: str) -> Optional[tuple[str, str]]:
    """Parse a template file under a skill's Templates/ directory.

    Returns (when, content) from the leading [#when] tag and the remaining
    body text; returns None if the file has no [#when] tag.
    """
    when = ""
    body_lines: list[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                m = _TAG_RE.match(line)
                if m and m.group(1) == "when":
                    when = (m.group(2) or "").strip()
                else:
                    body_lines.append(line)
    except Exception as e:
        print(f"[gen_skill] WARNING: Error reading template {path}: {e}", file=sys.stderr)
        return None

    if not when:
        print(f"[gen_skill] WARNING: Template {path} has no [#when] tag - skipping", file=sys.stderr)
        return None
    return when, expand_tabs("\n".join(body_lines).strip())


def collect_templates(skills: list[dict]) -> list[dict]:
    """Scan each skill directory for an optional Templates/ folder.

    Every *.md inside it must start with a [#when] tag describing when that
    template applies. Returns a list of {skill, pipeline, file, when, content}.
    """
    templates: list[dict] = []
    for s in skills:
        skill_dir = os.path.dirname(s["skill_path"])
        templates_dir = os.path.join(skill_dir, "Templates")
        if not os.path.isdir(templates_dir):
            continue
        for fname in sorted(os.listdir(templates_dir)):
            if not fname.lower().endswith(".md"):
                continue
            parsed = parse_template_file(os.path.join(templates_dir, fname))
            if parsed is None:
                continue
            when, content = parsed
            templates.append({
                "skill": s["sub_dir"],
                "pipeline": s["pipeline"],
                "file": fname,
                "when": when,
                "content": content,
            })
            print(f"[gen_skill] Template: {s['sub_dir']}/{fname} -> when={when}")
    return templates


def generate_template_table(templates: list[dict], lang: str) -> str:
    """Build the When | Template mapping table appended at the end of SKILL.md.

    The Template column is the template body serialized as a single-line JSON
    string (newlines as \\n, pipes escaped as \\|) so the markdown table stays
    well-formed. Parsers read the column as a JSON literal.
    """
    if not templates:
        return ""

    if lang == "zh":
        heading = "## 模板索引"
        header = "| 适用时机 (When) | 模板内容 (Template) |"
        note = (
            "> 模板内容为 JSON 转义的单行字符串：`\\n` 表示换行，`\\|` 表示字面量 `|`。"
            "读取时按 JSON 字符串解析即可还原原文。"
        )
    else:
        heading = "## Template Index"
        header = "| When | Template |"
        note = (
            "> Template cells are single-line JSON-escaped strings: `\\n` is a newline, "
            "`\\|` is a literal `|`. Parse as a JSON string to restore the original text."
        )

    sep = "|---|---|"
    parts = [heading, "", note, "", header, sep]
    for t in templates:
        single_line = json.dumps(t["content"], ensure_ascii=False).replace("|", "\\|")
        when_label = f"[{t['skill']}] {t['when']}"
        parts.append(f"| {when_label} | {single_line} |")
    return "\n".join(parts) + "\n"


def generate_workflow_with_content(skills: list[dict]) -> str:
    parts: list[str] = []

    for s in skills:
        parts.append(f"> {s['pipeline']}.{s['description']}")
        parts.append("")

        try:
            with open(s["skill_path"], "r", encoding="utf-8") as f:
                content = f.read()
            content = expand_tabs(content)
            content = demote_headings(content, levels=1)
            parts.append(content)
            parts.append("")
        except Exception as e:
            print(f"[gen_skill] WARNING: Error reading {s['skill_path']}: {e}", file=sys.stderr)

    return "\n".join(parts).rstrip("\n") + "\n"


def assemble_skill_md(skills: list[dict], templates: list[dict], lang: str) -> str:
    template_path, _ = get_paths(lang)
    if not os.path.isfile(template_path):
        print(f"[gen_skill] ERROR: TEMPLATE.md not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    if WORKFLOW_PLACEHOLDER not in template_content:
        print(f"[gen_skill] ERROR: Placeholder '{WORKFLOW_PLACEHOLDER}' not found in TEMPLATE.md", file=sys.stderr)
        sys.exit(1)

    workflow_md = generate_workflow_with_content(skills)
    template_content = template_content.replace(WORKFLOW_PLACEHOLDER, workflow_md, 1)

    # Append the When | Template mapping table at the very end of SKILL.md
    template_table = generate_template_table(templates, lang)
    if template_table:
        template_content = template_content.rstrip("\n") + "\n\n" + template_table

    return template_content


def main():
    # Cross-platform: force UTF-8 on stdout/stderr so Chinese output survives
    # Windows pipe redirection (MSBuild ConsoleToMSBuild, CI, etc.).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass  # Python < 3.7 or non-text stream: keep platform default

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
        print("[gen_skill] No skills with Meta.md found.")
        sys.exit(1)

    print(f"[gen_skill] Found {len(skills)} skill(s)")

    templates = collect_templates(skills)
    if templates:
        print(f"[gen_skill] Found {len(templates)} template(s)")

    full_content = assemble_skill_md(skills, templates, lang)

    # newline="\n" keeps the generated SKILL.md byte-identical across platforms.
    with open(skill_output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(full_content)

    print(f"[gen_skill] Generated: {skill_output_path}")
    print("[gen_skill] Done.")


if __name__ == "__main__":
    main()
