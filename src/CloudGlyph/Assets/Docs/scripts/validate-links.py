"""
validate-links.py

Deterministic, dependency-free validation of the link rules in the CloudGlyph
skill's 【Links & Navigation】 conventions. Use this in the skill's Review phase
instead of trusting the agent's eye.

A wiki page may only use three link kinds, and this script enforces them:
  1. External   -- `http(s):` / `mailto:` / `tel:`  → OK (opens in the OS browser)
  2. Same-language cross-page -- a relative path that resolves (honoring `.`/`..`)
     to another page DIRECTORY that holds an `index.md` inside the SAME language root
  3. In-page anchor -- `#slug` that equals the auto-generated heading slug of a real
     heading in the SAME file (lowercase; keep letters/digits/`_`/`-`, CJK kept;
     drop other chars; spaces & `_` → `-`; collapse/trim `-`; duplicates get `-1`, `-2`, …)

Links inside fenced code blocks and inline code spans are ignored. Raw-HTML `<a>`
tags and reference-style links are NOT scanned (documented limitation). Cross-page
targets carrying a `#` are rejected: the viewer would land on the page, not the anchor.

Usage:
    python validate-links.py                    # auto-detect content root
    python validate-links.py --lang en
    python validate-links.py <dir-or-file>

Exit code: 0 = clean, 1 = at least one ERROR.
"""

import argparse
import html
import posixpath
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "bin", "obj", "__pycache__"}
FENCE_RE = re.compile(r"^\s*```")
HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*$")
LINK_RE = re.compile(r"(!?\[[^\]\n]*\])\(\s*([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\s*\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*):")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


def plain_text(text: str) -> str:
    """Approximate the rendered plain text of a heading: strip inline code, links,
    emphasis markers and angle-bracket content, and unescape entities."""
    text = INLINE_CODE_RE.sub("", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # images first
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links → their text
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"[*_~]", "", text)
    text = html.unescape(text).strip()
    return text


def slugify(text: str) -> str:
    """Same rule as the renderer's auto heading-id generator."""
    t = plain_text(text).lower()
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)  # keep letters/digits/_/space/- (CJK kept)
    t = re.sub(r"[\s_]+", "-", t)
    t = re.sub(r"-+", "-", t)
    return t.strip("-")


def heading_ids(lines: list[str]) -> set[str]:
    """The set of anchor ids that exist in a file (duplicates resolved with -1, -2, …)."""
    used: set[str] = set()
    in_code = False
    for line in lines:
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = slugify(m.group(1))
        ident = base
        n = 1
        while ident in used:
            ident = f"{base}-{n}"
            n += 1
        used.add(ident)
    return used


def resolve_page_dir(rel_dir: str, dest: str) -> str | None:
    """Resolve a cross-page destination against *rel_dir* (the page dir relative to the
    language root) and return the target page-directory path, or None if it escapes the root
    or is not a directory-style target (e.g. a bare `.md` file that is not `index.md`)."""
    dest = dest.lstrip()
    base = "" if dest.startswith("/") else rel_dir
    dest = dest.lstrip("/")

    path = posixpath.normpath(posixpath.join(base, dest))
    if path == ".." or path.startswith("../"):
        return None  # escaped above the language root

    if path == "":
        return None  # the language root itself is not a page

    if path.endswith("/"):
        path = path.rstrip("/")
    if path.lower().endswith("/index.md"):
        path = path[: -len("/index.md")]
    if path == "":
        return None
    if path.lower().endswith(".md"):
        return None  # only index.md names a page directory

    return path


def validate_file(file: Path, root: Path) -> tuple[int, int]:
    errors = 0
    warnings = 0
    try:
        lines = file.read_text(encoding="utf-8").split("\n")
    except OSError as e:
        print(f"{file}: ERROR reading file: {e}")
        return 1, 0

    rel_dir = ""
    try:
        rel_dir = file.parent.relative_to(root).as_posix()
    except ValueError:
        pass

    anchors = heading_ids(lines)
    in_code = False
    for ln, raw in enumerate(lines, start=1):
        line = raw
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        prose = INLINE_CODE_RE.sub("", line)

        for token, dest in LINK_RE.findall(prose):
            if token.startswith("!"):
                continue  # image, not a link

            # 1) External
            m = SCHEME_RE.match(dest)
            if m:
                if m.group(1).lower() in EXTERNAL_SCHEMES:
                    continue
                errors += 1
                print(f"{file}:{ln}: ERROR unsupported scheme '{m.group(1)}:' in link -> {dest} (only http/https/mailto/tel may open externally)")
                continue

            # 2) In-page anchor
            if dest.startswith("#"):
                target = dest[1:]
                if target in anchors:
                    continue
                errors += 1
                print(f"{file}:{ln}: ERROR in-page anchor '#{target}' does not match any heading slug in this file (slug it from the exact heading text, see 【Links & Navigation】)")
                continue

            # 3) Same-language cross-page
            if "#" in dest:
                errors += 1
                print(f"{file}:{ln}: ERROR cross-page target must not carry a fragment -> {dest}")
                continue

            page_dir = resolve_page_dir(rel_dir, dest)
            if page_dir is None:
                errors += 1
                print(f"{file}:{ln}: ERROR link target does not resolve to a page directory inside the same language root -> {dest}")
                continue

            if (root / page_dir / "index.md").is_file():
                continue
            errors += 1
            print(f"{file}:{ln}: ERROR no page at '{page_dir}' (expected '{page_dir}/index.md' in the same language tree) -> {dest}")

    return errors, warnings


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Validate Markdown links against the CloudGlyph link rules")
    parser.add_argument("path", nargs="?", help="file or directory to scan (default: auto-detect content root)")
    parser.add_argument("--lang", help="only scan this language subdir (e.g. en, zh)")
    args = parser.parse_args()

    if args.path:
        target = Path(args.path)
    else:
        content = Path(__file__).resolve().parent.parent / "content"
        target = content / args.lang if args.lang else content

    # Language roots: the content root (holds languages_index.json) expands to its language
    # subdirs; any other directory is treated as a single language root.
    if target.is_dir():
        if (target / "languages_index.json").exists():
            roots = sorted(
                p for p in target.iterdir()
                if p.is_dir() and not p.name.startswith(".") and p.name not in SKIP_DIRS
            )
        else:
            roots = [target]
        files = sorted(f for root in roots for f in root.rglob("*.md"))
    elif target.is_file():
        roots = [target.parent]
        files = [target]
    else:
        print(f"ERROR: path not found: {target}", file=sys.stderr)
        sys.exit(2)

    total_errors = 0
    for f in files:
        errors, _warnings = validate_file(f, roots[0] if len(roots) == 1 else _root_for(f, roots))
        total_errors += errors

    print(f"[links] scanned {len(files)} file(s); {total_errors} error(s)")
    sys.exit(1 if total_errors else 0)


def _root_for(file: Path, roots: list[Path]) -> Path:
    """Pick the language root that contains *file* when scanning a content root."""
    file = file.resolve()
    for root in roots:
        try:
            file.relative_to(root)
            return root
        except ValueError:
            continue
    return roots[0]


if __name__ == "__main__":
    main()
