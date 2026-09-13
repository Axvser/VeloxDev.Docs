"""
validate-titles.py

Deterministic validation of the *reader-facing titles* of a wiki:

  1. **No numeric prefix in visible text.** `0_Welcome` / `1_QuickStart` /
     `00_user-registration` are directory names. The sidebar strips the prefix
     (`gen_tree.py`), so a hand-written `1_QuickStart` in a heading or a link
     label is always a defect — the reader sees two different names for one page.
     Checked surfaces: link labels, ATX heading text, and the inner text of an
     `<a>` element. Link *destinations* are exempt (a path keeps its prefix).
     Scanning skips fenced code blocks, inline code spans, `<style>` blocks and
     HTML comments — a prefix discussed inside a code span is deliberate.
     An uncoded occurrence in running prose is reported as a WARN, not an ERROR:
     prose about the directory layout is legitimate, but it should be written as
     `code` so it cannot be confused with a title.

  2. **Every page title is translated.** In a language tree that is not written
     in Latin script (detected from the tree's own directory names), the sidebar
     shows the directory name — so an untranslated segment is stray English in an
     otherwise translated wiki. Every ASCII letter run inside a segment must be a
     declared *code identifier* (a type / namespace / API name that must stay
     verbatim so readers can grep for it). `00_prerequisites` fails;
     `02_MVVM` passes once `MVVM` is declared.
     For a Latin-script language tree the rule cannot be applied by script, so
     the segment is instead compared with the base language's segment at the same
     position: an identical, undeclared segment is an ERROR.

Declared code identifiers live in `config/title-allowlist.json` next to the
content root (user-owned — a sync never overwrites it):

    {
      "codeIdentifiers": ["MVVM", "MonoBehaviour", "VeloxPropertyAttribute"]
    }

Matching is case-insensitive and whole-run: a segment is accepted when every
ASCII letter run in it is declared (built-in acronyms such as API, UI, MCP, DI,
SDK, HTTP are pre-declared).

Usage:
    python validate-titles.py                  # auto-detect content root
    python validate-titles.py --lang zh
    python validate-titles.py <dir-or-file>
    python validate-titles.py --base-lang en   # language to compare others against

Exit code: 0 = clean, 1 = at least one ERROR.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "bin", "obj", "__pycache__"}

_PREFIX_RE = re.compile(r"^(\d+)_")
# A numeric prefix that leaked into prose: `1_QuickStart`, `00_用户注册`.
# Requires a letter (any script) right after the underscore so `1_2` is ignored.
_PREFIX_TOKEN = re.compile(r"(?<![0-9A-Za-z_])\d{1,2}_(?=[A-Za-z_一-鿿])")

_FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")


def _fold_title(text: str) -> str:
    """Comparable form of a heading: lower-cased, separators collapsed."""
    return re.sub(r"[\s—–\-:：]+", " ", text).strip().lower()


def _squash(text: str) -> str:
    """Comparable form ignoring every separator: `Quick Start` == `QuickStart`."""
    return re.sub(r"[^0-9a-z一-鿿]+", "", text.lower())
_LINK_RE = re.compile(r"\[([^\]\n]*)\]\(([^)\n]*)\)")
_ANCHOR_RE = re.compile(r"<a\b[^>]*>(.*?)</a>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]*>")
_ASCII_RUN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")

# Acronyms that are code identifiers in essentially every project. Project-specific
# type/namespace names must be declared in config/title-allowlist.json.
BUILTIN_CODE_IDENTIFIERS = {
    "api", "se", "ui", "ux", "cli", "sdk", "mcp", "mvvm", "mvc", "aop", "di", "ioc",
    "io", "http", "https", "json", "xml", "yaml", "toml", "sql", "url", "uri",
    "id", "guid", "cpu", "gpu", "ram", "ssh", "tls", "ssl", "jwt", "oauth",
    "repl", "tui", "gui", "rest", "rpc", "grpc", "ci", "cd", "crud", "csv",
}


def _prefix_num(name: str):
    m = _PREFIX_RE.match(name)
    return int(m.group(1)) if m else None


def _strip_prefix(name: str) -> str:
    m = _PREFIX_RE.match(name)
    return name[m.end():] if m else name


def _blank(match) -> str:
    """Replace a match with the same number of newlines, preserving line numbers."""
    return "\n" * match.group(0).count("\n")


def _mask_non_visible(text: str) -> str:
    """Blank out everything whose content is not reader-facing title text."""
    out = []
    fence = None
    for line in text.split("\n"):
        m = _FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(2)
                out.append("")
            else:
                out.append(line)
        else:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
                fence = None
            out.append("")
    text = "\n".join(out)
    text = re.sub(r"<style\b.*?</style>", _blank, text, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", _blank, text, flags=re.S)
    # Inline code spans: a prefix inside `code` is deliberate, never a title.
    text = re.sub(r"`+[^`]*`+", "", text)
    return text


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_prefix_leaks(path: Path):
    """Return (errors, warnings) — lists of (line, message)."""
    errors: list[tuple[int, str]] = []
    warnings: list[tuple[int, str]] = []

    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as e:
        return [(0, f"cannot read file: {e}")], []

    text = _mask_non_visible(raw)

    def note(level, lineno, surface, token):
        msg = (f'numeric prefix in {surface}: "{token}" — visible text must read as the '
               f'page title without its numeric prefix (the sidebar renders exactly that, '
               f'so the same page would otherwise show two different names)')
        (errors if level == "ERROR" else warnings).append((lineno, msg))

    # Link labels (a destination keeps its prefix and is never scanned).
    for m in _LINK_RE.finditer(text):
        for tok in _tokens(m.group(1)):
            note("ERROR", _line_of(text, m.start()), "a link label", tok)

    # <a> inner text — the welcome page's clickable cards.
    for m in _ANCHOR_RE.finditer(text):
        inner = _TAG_RE.sub(" ", m.group(1))
        for tok in _tokens(inner):
            note("ERROR", _line_of(text, m.start()), "an <a> label", tok)

    # Headings.
    for lineno, line in enumerate(text.split("\n"), 1):
        hm = _HEADING_RE.match(line)
        if hm:
            for tok in _tokens(hm.group(2)):
                note("ERROR", lineno, "a heading", tok)

    # Remaining running prose — reported, but only as a WARN.
    residual = _LINK_RE.sub(" ", text)
    residual = _ANCHOR_RE.sub(" ", residual)
    residual = "\n".join(
        _HEADING_RE.sub(" ", line) for line in residual.split("\n")
    )
    for tok in _tokens(residual):
        lineno = _line_of(residual, residual.find(tok))
        note("WARN", lineno,
             "prose (wrap it in `code` if you are discussing the directory itself)", tok)

    return errors, warnings


def scan_heading_repetition(path: Path):
    """A heading that restates the heading above it, with no content in between.

    This is the "triple title" shape — `# Workflow System — Quick Start` followed by
    `## Workflow System` followed by `### Quick Start` — where a reader meets the same
    words three times before any content. A heading may restate a *parent* dimension it
    sits under (the sidebar already says where you are), and it may not restate the
    heading it directly follows.
    """
    errors: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").split("\n")
    except OSError:
        return errors

    heads = []
    fence = None
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(2)
            continue
        h = _HEADING_RE.match(line)
        if h:
            heads.append((len(h.group(1)), h.group(2), i))

    if not heads:
        return errors

    # The dimension this page lives under, e.g. `1_QuickStart` -> "quickstart".
    grand = path.parent.parent
    dim = _squash(_strip_prefix(grand.name)) if grand != path.parent else ""

    for above, below in zip(heads, heads[1:]):
        if any(x.strip() for x in lines[above[2] + 1:below[2]]):
            continue                       # real content separates them
        a, b = _fold_title(above[1]), _fold_title(below[1])
        restates = bool(b) and (a == b or a.startswith(b + " ") or b.startswith(a + " "))
        names_dimension = bool(dim) and _squash(below[1]) == dim
        if restates or names_dimension:
            why = "restates the heading above it" if restates else "only names the parent dimension"
            errors.append((
                below[2] + 1,
                f'heading "#{below[0]} {below[1]}" {why} and has no content between them — '
                f'the page title already says this. Delete it and promote what it contains.',
            ))
    return errors


def _tokens(text: str) -> list[str]:
    """Every full `NN_name` token in *text*, e.g. `1_QuickStart`, `00_用户注册`."""
    out = []
    for m in _PREFIX_TOKEN.finditer(text):
        tail = text[m.start():]
        full = re.match(r"\d{1,2}_[0-9A-Za-z_\-一-鿿]*", tail)
        out.append(full.group(0) if full else tail[:12])
    return out


def load_allowlist(config_dir: Path, explicit: str | None) -> tuple[set[str], str | None]:
    """Return (declared identifiers, path used). Built-ins are always merged in."""
    path = Path(explicit) if explicit else config_dir / "title-allowlist.json"
    declared = set()
    used = None
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
            values = doc.get("codeIdentifiers", doc if isinstance(doc, list) else [])
            declared = {str(v).lower() for v in values}
            used = str(path)
        except (OSError, ValueError, AttributeError) as e:
            print(f"[titles] WARN cannot read allowlist {path}: {e}")
    return BUILTIN_CODE_IDENTIFIERS | declared, used


def lang_roots(target: Path, lang: str | None) -> list[Path]:
    if target.is_file():
        return [target.parent]
    if (target / "languages_index.json").exists():
        roots = sorted(
            p for p in target.iterdir()
            if p.is_dir() and not p.name.startswith(".") and p.name not in SKIP_DIRS
        )
    else:
        roots = [target]
    if lang:
        roots = [r for r in roots if r.name == lang]
    return roots


def page_dirs(root: Path) -> dict[tuple, str]:
    """Map numeric-prefix topology -> directory segment name for every page dir."""
    result: dict[tuple, str] = {}
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in SKIP_DIRS]
        for d in dirnames:
            full = Path(dirpath) / d
            if not (full / "index.md").is_file():
                continue  # not a page directory (validate-structure.py owns that gate)
            rel = full.relative_to(root)
            key = tuple(_prefix_num(p) for p in rel.parts)
            if any(k is None for k in key):
                continue
            result[key] = d
    return result


def is_latin_script(root: Path) -> bool:
    """True when the tree's own directory names are all ASCII (an en/de/fr-style tree)."""
    names = [p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if not names:
        return True
    return all(name.isascii() for name in names)


def check_translation(root: Path, allow: set[str], base_dirs: dict | None):
    """Return a list of (relpath, message) for untranslated page titles."""
    problems = []
    dirs = page_dirs(root)
    latin = is_latin_script(root)

    for key, name in sorted(dirs.items(), key=lambda kv: kv[0]):
        title = _strip_prefix(name)
        rel = "/".join(name for name in
                       [dirs.get(key[: i + 1], "?") for i in range(len(key))])

        if not latin:
            # Every ASCII letter run must be a declared code identifier.
            undeclared = [run for run in _ASCII_RUN_RE.findall(title)
                          if run.lower() not in allow]
            if undeclared:
                problems.append((
                    rel,
                    f'"{title}" is not translated — undeclared English word(s) '
                    f'{", ".join(repr(u) for u in undeclared)}. Translate the segment, or '
                    f'declare it in config/title-allowlist.json if it is a type / '
                    f'namespace / API name from the source.',
                ))
        elif base_dirs is not None:
            # Latin-script tree: an identical, undeclared segment is a copy of the base.
            counterpart = base_dirs.get(key)
            if (counterpart is not None
                    and _strip_prefix(counterpart).lower() == title.lower()
                    and not all(run.lower() in allow for run in _ASCII_RUN_RE.findall(title))):
                problems.append((
                    rel,
                    f'"{title}" is identical to the base-language title — it looks '
                    f'untranslated. Translate it, or declare it in '
                    f'config/title-allowlist.json if it is a code identifier.',
                ))
    return problems


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Validate wiki page titles (prefix leaks, translation)")
    parser.add_argument("path", nargs="?", help="file or directory to scan (default: auto-detect content root)")
    parser.add_argument("--lang", help="only scan this language subdir (e.g. en, zh)")
    parser.add_argument("--base-lang", default="en",
                        help="language other trees are compared against (default: en)")
    parser.add_argument("--allowlist", help="path to title-allowlist.json")
    args = parser.parse_args()

    if args.path:
        target = Path(args.path)
    else:
        target = Path(__file__).resolve().parent.parent / "content"

    if not target.exists():
        print(f"[titles] ERROR path not found: {target} (pass a content root explicitly)")
        sys.exit(1)

    config_dir = target.parent / "config" if (target / "languages_index.json").exists() else target.parent
    allow, allow_path = load_allowlist(config_dir, args.allowlist)
    if allow_path:
        print(f"[titles] allowlist: {allow_path}")

    roots = lang_roots(target, args.lang)
    if not roots:
        print("[titles] ERROR no language root to scan")
        sys.exit(1)

    total_errors = total_warns = 0
    warnings: list[str] = []

    # 1. Numeric prefixes leaking into reader-facing text, and headings that
    #    restate the heading above them.
    files = sorted({p for r in roots for p in ([r] if r.is_file() else r.rglob("*.md"))})
    for f in files:
        errors, warns = scan_prefix_leaks(f)
        errors += scan_heading_repetition(f)
        for lineno, msg in errors:
            total_errors += 1
            print(f"{f}:{lineno}: ERROR {msg}")
        for lineno, msg in warns:
            total_warns += 1
            warnings.append(f"{f}:{lineno}: WARN  {msg}")

    # 2. Untranslated page titles.
    base_dirs = None
    if len(roots) > 1 or not (len(roots) == 1 and roots[0].name == args.base_lang):
        for r in roots:
            if r.is_file():
                continue
            if r.name == args.base_lang:
                base_dirs = page_dirs(r)
                break
    for r in roots:
        if r.is_file() or r.name == args.base_lang:
            continue
        for rel, msg in check_translation(r, allow, base_dirs):
            total_errors += 1
            print(f"{r.name}/{rel}: ERROR {msg}")

    for line in warnings:
        print(line)

    print(f"[titles] scanned {len(files)} file(s) across {len(roots)} language root(s); "
          f"{total_errors} error(s), {total_warns} warning(s)")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
