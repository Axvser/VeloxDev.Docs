"""
gen_tree.py

Scans each language directory under Assets/Docs/content/ for index.md files,
builds a hierarchical tree.json index used by the Avalonia Markdown viewer.
Pages are ordered by directory name; numeric prefixes like "1_QuickStart"
are stripped in the displayed title but preserved in the path for file loading.
"""

import json
import os
import re
import sys

# __file__ is under scripts/, so content/ is two levels up: ../../
CONTENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "content"))

# Directories to skip when scanning for language roots
_SKIP = {"__pycache__"}

# Matches leading "N_" or "NN_" prefix (e.g. "1_", "12_")
_PREFIX_RE = re.compile(r"^\d+_(.+)$")


def _title(name: str) -> str:
    """Strip numeric prefix from a directory name to get the display title.
    e.g. "1_QuickStart" → "QuickStart", "Welcome" → "Welcome".
    """
    m = _PREFIX_RE.match(name)
    return m.group(1) if m else name


def _ensure_index_md(dir_path: str) -> None:
    """Create a blank index.md if missing. This ensures the directory
    appears in the navigation tree even when content hasn't been written yet.
    """
    index_path = os.path.join(dir_path, "index.md")
    if not os.path.isfile(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"[gen_tree] Created blank: {index_path}")


def _scan(dir_path: str, lang_root: str) -> list[dict]:
    """Scan *dir_path* for subdirectories that contain index.md and return
    them as a list of ``{title, path, children}`` dicts.

    Sorting is natural (OS order) — use numeric prefixes to control sequence.
    *lang_root* is the language root — paths are computed relative to it.
    Missing index.md files are auto-created as blank.
    """
    nodes: list[dict] = []
    for entry in sorted(os.listdir(dir_path)):
        child_path = os.path.join(dir_path, entry)
        if not os.path.isdir(child_path):
            continue
        _ensure_index_md(child_path)

        rel_path = os.path.relpath(child_path, lang_root).replace("\\", "/")
        children = _scan(child_path, lang_root)

        nodes.append({
            "title": _title(entry),
            "path": rel_path,
            "children": children,
        })
    return nodes


def main():
    # Cross-platform: force UTF-8 on stdout/stderr so Chinese paths survive
    # Windows pipe redirection (MSBuild ConsoleToMSBuild, CI, etc.).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    for lang in sorted(os.listdir(CONTENT_DIR)):
        lang_dir = os.path.join(CONTENT_DIR, lang)
        if not os.path.isdir(lang_dir):
            continue
        if lang.startswith(".") or lang in _SKIP:
            continue

        pages: list[dict] = []
        for entry in sorted(os.listdir(lang_dir)):
            child_path = os.path.join(lang_dir, entry)
            if not os.path.isdir(child_path):
                continue
            _ensure_index_md(child_path)

            children = _scan(child_path, lang_dir)
            pages.append({
                "title": _title(entry),
                "path": entry,
                "children": children,
            })

        tree = {"Pages": pages}
        tree_path = os.path.join(lang_dir, "tree.json")
        # newline="\n" keeps tree.json byte-identical across platforms.
        with open(tree_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        n = len(pages)
        print(f"[gen_tree] Updated: {tree_path} ({n} root pages)")


if __name__ == "__main__":
    main()
