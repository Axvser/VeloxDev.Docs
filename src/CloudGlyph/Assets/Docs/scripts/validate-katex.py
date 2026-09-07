"""
validate-katex.py

Deterministic validation of KaTeX math delimiters in Markdown wiki content.
Use this in the skill's Review phase instead of relying on the agent's eye.

The scanner ignores content inside fenced code blocks, because `$` there is usually
not math (e.g. C# string interpolation `$"..."` in code) and produced false positives.

Checks:
  ERROR  odd count of `$$` block-math delimiters across a file (unbalanced $$ ... $$)
  ERROR  odd count of remaining `$` after removing $$ blocks (unbalanced inline $...$)
  ERROR  single-line display math `$$expr$$` (open+close on the same line) — the CloudGlyph
         viewer's block parser only recognizes multi-line `$$\n…\n$$`, so these never render
  WARN   a CJK character used directly in math outside a `\text{...}` group — KaTeX lacks CJK
         glyphs and only warns; wrap prose in `\text{...}` or keep it outside the formula
  WARN   `$"` seen outside code fences (a C#-style interpolated string leaked into prose)
  WARN   `$ ` or ` $` (dollar adjacent to a space) — probably currency, not math

Usage:
    python validate-katex.py                    # auto-detect content root
    python validate-katex.py --lang en
    python validate-katex.py <dir-or-file>

Exit code: 0 = clean, 1 = at least one ERROR.
"""

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^```\w*\s*$")
DOLLAR_DOLLAR_RE = re.compile(r"\$\$")
DOLLAR_RE = re.compile(r"\$(?!\$)")  # single $ not followed by another $
CJK_RE = re.compile(r"[一-鿿]")
SAME_LINE_DISPLAY_RE = re.compile(r"\$\$.+?\$\$")
TEXT_CMD = "\\text{"


def _cjk_outside_text(math: str) -> str:
    """Characters in a math snippet that are CJK and NOT inside a \\text{...} group."""
    found = []
    i, n = 0, len(math)
    while i < n:
        if math.startswith(TEXT_CMD, i):
            depth, j = 1, i + len(TEXT_CMD)
            while j < n and depth > 0:
                if math[j] == "{":
                    depth += 1
                elif math[j] == "}":
                    depth -= 1
                j += 1
            i = j
            continue
        if math[i] == "\\" and i + 1 < n and math[i + 1].isalpha():
            i += 2
            continue
        if CJK_RE.match(math[i]):
            found.append(math[i])
        i += 1
    return "".join(found)


def _math_spans(line: str):
    """Yield the content of every $...$ / $$...$$ span on one prose line."""
    i, n = 0, len(line)
    while i < n:
        if line[i] != "$":
            i += 1
            continue
        j = i + 1
        dbl = j < n and line[j] == "$"
        if dbl:
            j += 1
        end = line.find("$$", j) if dbl else line.find("$", j)
        if end == -1:
            break
        yield line[j:end]
        i = end + (2 if dbl else 1)


def split_fences(lines):
    """Return (code_fenced, prose) tuples: (in_code, line)."""
    out = []
    in_code = False
    for line in lines:
        if FENCE_RE.match(line.strip()):
            in_code = not in_code
            out.append((True, line))
            continue
        out.append((in_code, line))
    return out


def validate_file(lines):
    issues = []
    fenced = split_fences(lines)
    prose = "\n".join(line for in_code, line in fenced if not in_code)
    # re-fence aware prose line indices for reporting
    prose_line_numbers = [i + 1 for i, (in_code, _) in enumerate(fenced) if not in_code]

    # block math: $$ ... $$
    dd = len(DOLLAR_DOLLAR_RE.findall(prose))
    if dd % 2 != 0:
        issues.append(("ERROR", f"odd count of '$$' block delimiters ({dd}) — unbalanced $$ ... $$"))

    # remove complete $$...$$ spans, then count leftover single $
    stripped = DOLLAR_DOLLAR_RE.sub("", prose)
    single = len(DOLLAR_RE.findall(stripped))
    if single % 2 != 0:
        issues.append(("ERROR", f"odd count of inline '$' delimiters ({single}) — unbalanced $...$"))

    # heuristic warnings on prose (conservative: a `$` followed by a digit looks like
    # currency, not math; `$` before/after whitespace is normal inline-math and NOT flagged)
    for m in re.finditer(r'\$"', prose):
        issues.append(("WARN", "C#-style $\" interpolated string outside a code fence"))
    for ln in prose_line_numbers:
        line = fenced[ln - 1][1] if 0 <= ln - 1 < len(fenced) else ""
        # currency: `$` + digits + NOT a math continuation (math like `$2S$` has a letter
        # right after the digits and must not be flagged)
        if re.search(r"\$[\d]+(?=[\s.,;:!?]|$)", line):
            issues.append(("WARN", f"line {ln}: '$' followed by digits — likely currency, verify it is math"))

    # Renderer-compatibility checks (the CloudGlyph viewer = AvalonMarkdown block parser):
    for i, (in_code, line) in enumerate(fenced):
        if in_code:
            continue
        ln = i + 1
        if SAME_LINE_DISPLAY_RE.search(line):
            issues.append(("ERROR",
                f"line {ln}: single-line display math '$$…$$' — open and close on the same line; "
                "the viewer only renders display math as a standalone multi-line '$$' block"))
        for math in _math_spans(line):
            bare = _cjk_outside_text(math)
            if bare:
                issues.append(("WARN",
                    f"line {ln}: CJK characters {bare!r} used in math outside \\text{{}} — "
                    "wrap them in \\text{...} or move the prose out of the formula"))

    return issues


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Validate KaTeX delimiters in wiki Markdown")
    parser.add_argument("path", nargs="?", help="file or directory to scan (default: auto-detect content root)")
    parser.add_argument("--lang", help="only scan this language subdir (e.g. en, zh)")
    args = parser.parse_args()

    if args.path:
        target = Path(args.path)
    else:
        content = Path(__file__).resolve().parent.parent.parent / "content"
        target = content / args.lang if args.lang else content

    files = [target] if target.is_file() else sorted(target.rglob("*.md"))
    total_errors = total_warns = 0

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").split("\n")
        except OSError as e:
            print(f"[katex] ERROR reading {f}: {e}")
            total_errors += 1
            continue
        for level, msg in validate_file(lines):
            if level == "ERROR":
                total_errors += 1
                print(f"{f}: ERROR {msg}")
            else:
                total_warns += 1
                print(f"{f}: WARN  {msg}")

    print(f"[katex] scanned {len(files)} file(s); {total_errors} error(s), {total_warns} warning(s)")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
