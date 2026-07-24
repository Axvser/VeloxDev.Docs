"""
gen_lang_index.py

Scans the Assets/Docs/content/ directory for language subdirectories, cross-references
them against the master config/languages.json mapping, and writes
content/languages_index.json - which is then embedded as an AvaloniaResource
at build time.
"""

import json
import os
import sys

# __file__ is under scripts/, so go up one level to reach Assets/Docs/
DOCS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Language doc directories live under content/
CONTENT_DIR = os.path.join(DOCS_ROOT, "content")


# Directories to skip (dot-directories, cache)
_SKIP_DIRS = {"__pycache__"}


def main():
    master_path = os.path.join(DOCS_ROOT, "config", "languages.json")
    if not os.path.isfile(master_path):
        print(
            f"[gen_lang_index] ERROR: languages.json not found at "
            f"{master_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(master_path, "r", encoding="utf-8") as f:
        master: dict[str, str] = json.load(f)

    found: list[dict[str, str]] = []
    for entry in sorted(os.listdir(CONTENT_DIR)):
        if entry.startswith("."):
            continue
        if entry in _SKIP_DIRS:
            continue
        lang_dir = os.path.join(CONTENT_DIR, entry)
        if not os.path.isdir(lang_dir):
            continue
        # Must contain at least one index.md to be a valid language doc tree
        if not _has_markdown(lang_dir):
            continue

        display_name = master.get(entry, entry)
        found.append({"code": entry, "displayName": display_name})

    indexPath = os.path.join(CONTENT_DIR, "languages_index.json")
    with open(indexPath, "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)

    print(
        f"[gen_lang_index] Updated: {indexPath} "
        f"({len(found)} languages)"
    )


def _has_markdown(dir_path: str) -> bool:
    """Check if *dir_path* or any subdirectory contains an index.md file."""
    for root, _dirs, files in os.walk(dir_path):
        if "index.md" in files:
            return True
    return False


if __name__ == "__main__":
    main()
