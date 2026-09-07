"""
claude_install.py

Installs the assembled SKILL.md into a target Claude code working directory.

Usage:
    python skills/claude_install.py /path/to/.claude
    python skills/claude_install.py /path/to/.claude --lang zh
    python skills/claude_install.py                  # prompt for dir

The script will:
1. Run gen_skill.py to produce the latest SKILL.md
2. Copy/overwrite to .claude/skills/cloud-glyph-wiki-create/SKILL.md
"""

import argparse
import os
import shutil
import subprocess
import sys

SKILLS_ROOT = os.path.abspath(os.path.dirname(__file__))
SKILL_OUTPUT = os.path.join(SKILLS_ROOT, "SKILL.md")
GEN_SCRIPT = os.path.join(SKILLS_ROOT, "gen_skill.py")

# The fixed skill name under .claude/skills/
SKILL_NAME = "cloud-glyph-wiki-create"


def regenerate_skill(lang: str) -> None:
    """Run gen_skill.py for the given language to produce the latest SKILL.md."""
    if not os.path.isfile(GEN_SCRIPT):
        print(f"[claude_install] ERROR: gen_skill.py not found at {GEN_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    print(f"[claude_install] Regenerating SKILL.md (lang={lang})...")
    result = subprocess.run(
        [sys.executable, GEN_SCRIPT, "--lang", lang],
        capture_output=True,
        text=True,
        encoding="utf-8",  # gen_skill.py emits UTF-8 on stdout (see its main())
        errors="replace",  # never crash on undecodable bytes
        cwd=SKILLS_ROOT,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0:
        print(f"[claude_install] ERROR: gen_skill.py failed (exit code {result.returncode})", file=sys.stderr)
        sys.exit(1)


def install(claude_root: str, lang: str) -> None:
    """Copy SKILL.md into .claude/skills/{SKILL_NAME}/SKILL.md under claude_root,
    then ship each module's pristine Templates/*.md next to it.

    The aggregated SKILL.md embeds template bodies as JSON-escaped table cells (for
    agents whose skill loader accepts a single file). Shipping the raw files as well
    gives agents that CAN read sibling files (Claude skills, for example) the exact
    original template with no decode step — see the welcome-page module's
    "Raw file (preferred)" note.
    """
    target_dir = os.path.join(claude_root, "skills", SKILL_NAME)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "SKILL.md")

    shutil.copy2(SKILL_OUTPUT, target_path)
    print(f"[claude_install] Installed: {target_path}")

    # Copy skills/<lang>/<module>/Templates/*.md into <target>/Templates/.
    # Flat filename first; on collision fall back to Templates/<module>/<file>.
    lang_root = os.path.join(SKILLS_ROOT, lang)
    seen: set[str] = set()
    if os.path.isdir(lang_root):
        for module in sorted(os.listdir(lang_root)):
            templates_dir = os.path.join(lang_root, module, "Templates")
            if not os.path.isdir(templates_dir):
                continue
            for fname in sorted(os.listdir(templates_dir)):
                if not fname.lower().endswith(".md"):
                    continue
                src = os.path.join(templates_dir, fname)
                if fname in seen:
                    dst_dir = os.path.join(target_dir, "Templates", module)
                    os.makedirs(dst_dir, exist_ok=True)
                    dst = os.path.join(dst_dir, fname)
                    print(f"[claude_install] Template (collision): {dst}")
                else:
                    seen.add(fname)
                    dst_dir = os.path.join(target_dir, "Templates")
                    os.makedirs(dst_dir, exist_ok=True)
                    dst = os.path.join(dst_dir, fname)
                shutil.copy2(src, dst)
                print(f"[claude_install] Template: {dst}")
    else:
        print(f"[claude_install] WARNING no skills/{lang} module tree to ship templates from", file=sys.stderr)

    # Ship the independent reviewer agent definition so the installed skill can hand
    # its Review phase to a sub-agent that did not write the content (see the Review
    # module's "Reviewer Assignment"). Placed under <claude_root>/agents/wiki-reviewer.md.
    reviewer_src = os.path.join(SKILLS_ROOT, "wiki-reviewer.md")
    if os.path.isfile(reviewer_src):
        agents_dir = os.path.join(claude_root, "agents")
        os.makedirs(agents_dir, exist_ok=True)
        reviewer_dst = os.path.join(agents_dir, "wiki-reviewer.md")
        shutil.copy2(reviewer_src, reviewer_dst)
        print(f"[claude_install] Agent: {reviewer_dst}")
    else:
        print(f"[claude_install] WARNING wiki-reviewer.md not found next to the installer", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Install assembled SKILL.md into a Claude code working directory")
    parser.add_argument(
        "claude_dir",
        nargs="?",
        default=None,
        help="Path to the .claude directory or project root. If omitted, the script will prompt.",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Language to generate before installing (e.g. 'en', 'zh'). Default: en",
    )
    args = parser.parse_args()

    raw_dir = args.claude_dir
    if not raw_dir:
        raw_dir = input("Enter the .claude directory path: ").strip()

    if not os.path.isdir(raw_dir):
        print(f"[claude_install] ERROR: Directory not found: {raw_dir}", file=sys.stderr)
        sys.exit(1)

    # Normalize: determine claude_root based on the input path
    raw_normalized = os.path.normpath(raw_dir).rstrip(os.sep + "/")
    # Split path components to detect known suffixes
    parts = raw_normalized.split(os.sep)
    if len(parts) >= 2 and parts[-2] == ".claude" and parts[-1] == "skills":
        # e.g. /home/user/.claude/skills — install into .claude/
        claude_root = os.path.dirname(raw_normalized)
    elif parts[-1] == ".claude":
        # e.g. /home/user/.claude — use directly
        claude_root = raw_normalized
    else:
        # e.g. /home/user/project — create .claude/ under it
        claude_root = os.path.join(raw_normalized, ".claude")

    print(f"[claude_install] Target root: {claude_root}")
    print(f"[claude_install] Language: {args.lang}")

    # 1. Regenerate SKILL.md
    regenerate_skill(args.lang)

    # 2. Copy to target
    install(claude_root, args.lang)

    print("[claude_install] Done.")


if __name__ == "__main__":
    main()
