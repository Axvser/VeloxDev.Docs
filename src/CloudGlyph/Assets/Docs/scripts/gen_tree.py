"""
gen_tree.py

Scans each language directory under Assets/Docs/content/ for index.md files,
builds a hierarchical tree.json index used by the Avalonia Markdown viewer.
Pages are ordered by directory name; numeric prefixes like "1_QuickStart"
are stripped in the displayed title but preserved in the path for file loading.

Directory hygiene (enforced by validate-structure.py, mirrored here):
  * A directory that does NOT contain an index.md is NOT a page. It is skipped
    (with a WARNING) rather than silently auto-created, so an author who forgets
    an index.md can no longer hide behind this generator.
  * --strict turns any such skip into a non-zero exit code (used by the Review
    gate / CI); without it the build still succeeds so a half-finished tree does
    not break local compilation.
"""

import argparse
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


def _scan(dir_path: str, lang_root: str, missing: list[str]) -> list[dict]:
    """Scan *dir_path* for subdirectories that contain index.md and return
    them as a list of ``{title, path, children}`` dicts.

    Sorting is natural (OS order) — use numeric prefixes to control sequence.
    *lang_root* is the language root — paths are computed relative to it.
    Subdirectories lacking an index.md are NOT page directories: they are
    recorded in *missing*, warned about, and skipped (never auto-created).
    """
    nodes: list[dict] = []
    for entry in sorted(os.listdir(dir_path)):
        child_path = os.path.join(dir_path, entry)
        if not os.path.isdir(child_path):
            continue

        rel_path = os.path.relpath(child_path, lang_root).replace("\\", "/")
        if not os.path.isfile(os.path.join(child_path, "index.md")):
            missing.append(rel_path)
            print(f"[gen_tree] WARNING no index.md in {rel_path} — directory omitted from the tree"
                  f" (add an index.md, even an empty one; see validate-structure.py)")
            continue

        children = _scan(child_path, lang_root, missing)
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
            pass  # Python < 3.7 or non-text stream: keep platform default

    parser = argparse.ArgumentParser(description="Build tree.json per language from index.md directories")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if any directory lacks an index.md (quality gate)")
    parser.add_argument("--lang", help="only process one language subdir (e.g. en, zh)")
    args = parser.parse_args()

    languages = [d for d in sorted(os.listdir(CONTENT_DIR))
                 if os.path.isdir(os.path.join(CONTENT_DIR, d))
                 and not d.startswith(".")
                 and d not in _SKIP]
    if args.lang:
        languages = [l for l in languages if l == args.lang]

    total_missing = 0
    for lang in languages:
        lang_dir = os.path.join(CONTENT_DIR, lang)

        pages: list[dict] = []
        missing: list[str] = []
        for entry in sorted(os.listdir(lang_dir)):
            child_path = os.path.join(lang_dir, entry)
            if not os.path.isdir(child_path):
                continue
            rel = entry
            if not os.path.isfile(os.path.join(child_path, "index.md")):
                missing.append(rel)
                print(f"[gen_tree] WARNING no index.md in {rel} — directory omitted from the tree"
                      f" (add an index.md, even an empty one; see validate-structure.py)")
                continue
            children = _scan(child_path, lang_dir, missing)
            pages.append({
                "title": _title(entry),
                "path": rel,
                "children": children,
            })

        total_missing += len(missing)

        tree = {"Pages": pages}
        tree_path = os.path.join(lang_dir, "tree.json")
        # newline="\n" keeps tree.json byte-identical across platforms.
        with open(tree_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        n = len(pages)
        extra = f" ({len(missing)} dir(s) skipped: missing index.md)" if missing else ""
        print(f"[gen_tree] Updated: {tree_path} ({n} root pages){extra}")

    print(f"[gen_tree] {len(languages)} language(s) processed; {total_missing} directory(ies) missing index.md")
    if args.strict and total_missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
