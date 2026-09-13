"""
validate-plot.py

Deterministic structural validation of ```plot fences in Markdown wiki content.
Use this in the skill's Review phase instead of relying on the agent's eye.

A ```plot body is a JSON object consumed by the function-plot library through the
renderer's hydration step. Every failure below is SILENT in the viewer: a broken
body renders an inline error block, a rejected expression draws nothing, and a
non-linear graph type without the built-in sampler throws inside the library with
no console output. There is no visual clue beyond the curve being absent.

Checks (per ```plot fenced block):
  ERROR  body is valid JSON
  ERROR  body is a single JSON object
  ERROR  "data" is present and is an array
  ERROR  every datum is an object
  ERROR  each expression string ("fn" / "x" / "y" / "r") uses only the characters
         the renderer's whitelist accepts -- quotes, semicolons, braces, brackets
         and backslashes are rejected before the expression reaches the evaluator
  ERROR  a non-linear datum ("fnType" parametric/polar/points/vector, or
         "graphType" scatter) carries "sampler": "builtIn"
  WARN   "data" is missing entirely -- the plot draws bare axes
  WARN   a lower-case "pi" token -- constants are upper-case (PI, E); lower-case
         forms are undefined and the series silently fails to draw

Usage:
    python validate-plot.py                  # auto-detect content root
    python validate-plot.py --lang en
    python validate-plot.py <dir-or-file>

Exit code: 0 = clean, 1 = at least one ERROR.
"""

import argparse
import json
import re
import sys
from pathlib import Path

_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([^\s`~]*)\s*$")

# Mirrors PLOT_FN_WHITELIST in AvalonMarkdown's render_check.py, which in turn
# mirrors plotExpressionError() in the renderer. Anything outside it is rejected
# outright by the renderer.
PLOT_FN_WHITELIST = re.compile(r"[0-9A-Za-z_+\-*/^().,\s%?:<>=!]*")

PLOT_EXPR_KEYS = ("fn", "x", "y", "r")

# Graph types whose evaluator is not the default interval sampler. Using one of
# these without "sampler": "builtIn" throws inside function-plot.
NEEDS_BUILTIN_SAMPLER = frozenset({"parametric", "polar", "points", "vector"})

# A bare lower-case pi token: `pi` not preceded/followed by an identifier char.
# (`exp`, `skip`, an identifier named `pi2` … must not match.)
_LOWER_PI_RE = re.compile(r"(?<![A-Za-z0-9_])pi(?![A-Za-z0-9_])")


def find_plot_blocks(lines):
    """Yield (open_line_index, body_lines) for every ```plot fence in *lines*.

    Handles nested-length fences (a 4-backtick fence wrapping a 3-backtick one),
    which is how the skill's own docs show a plot example inside Markdown.
    """
    i = 0
    while i < len(lines):
        m = _FENCE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        ticks, info = m.group(2), m.group(3)
        if info.lower() != "plot":
            i += 1
            continue
        close_re = re.compile(r"^\s*" + re.escape(ticks[0]) + "{" + str(len(ticks)) + r",}\s*$")
        j = i + 1
        while j < len(lines) and not close_re.match(lines[j]):
            j += 1
        yield i, lines[i + 1 : j]
        i = j + 1


def check_block(body_lines):
    """Return a list of (level, message) for one plot block body."""
    issues = []
    raw = "\n".join(body_lines).strip()
    if not raw:
        return [("ERROR", "empty plot block")]

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        return [("ERROR", f"plot body is not valid JSON ({e}); the renderer shows an "
                          f"inline error block instead of a curve")]

    if not isinstance(doc, dict):
        return [("ERROR", 'the plot body must be a single JSON object, e.g. {"data": [...]}')]

    if "data" not in doc:
        return [("WARN", 'plot has no "data"; it will draw bare axes')]

    data = doc["data"]
    if not isinstance(data, list):
        return [("ERROR", f'"data" must be an array, got {type(data).__name__}')]

    # The renderer skips expression validation for a non-array "data", so every
    # check below only runs once we know it is an array.
    for idx, datum in enumerate(data):
        if not isinstance(datum, dict):
            issues.append(("ERROR", f'"data[{idx}]" must be an object, got {type(datum).__name__}'))
            continue

        for key in PLOT_EXPR_KEYS:
            val = datum.get(key)
            if isinstance(val, str) and not PLOT_FN_WHITELIST.fullmatch(val):
                bad = sorted({c for c in val if not PLOT_FN_WHITELIST.fullmatch(c)})
                issues.append((
                    "ERROR",
                    f'"data[{idx}].{key}" contains character(s) the renderer rejects: '
                    f"{' '.join(repr(c) for c in bad)} — quotes, semicolons, braces, brackets "
                    f"and backslashes are not allowed in plot expressions",
                ))

        fn_type = str(datum.get("fnType", "")).lower()
        graph_type = str(datum.get("graphType", "")).lower()
        needs_sampler = fn_type in NEEDS_BUILTIN_SAMPLER or graph_type == "scatter"
        if needs_sampler and datum.get("sampler") != "builtIn":
            what = f'fnType "{fn_type}"' if fn_type in NEEDS_BUILTIN_SAMPLER else 'graphType "scatter"'
            issues.append((
                "ERROR",
                f'"data[{idx}]" uses {what} without "sampler": "builtIn" — the default '
                f"interval sampler does not support it and the series silently disappears",
            ))

        for key in PLOT_EXPR_KEYS:
            val = datum.get(key)
            if isinstance(val, str) and _LOWER_PI_RE.search(val):
                issues.append((
                    "WARN",
                    f'"data[{idx}].{key}" uses lower-case "pi"; constants are upper-case '
                    f"(PI, E) and the lower-case form is undefined — the curve will not draw",
                ))

    return issues


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Validate plot fences in wiki Markdown")
    parser.add_argument("path", nargs="?", help="file or directory to scan (default: auto-detect content root)")
    parser.add_argument("--lang", help="only scan this language subdir (e.g. en, zh)")
    args = parser.parse_args()

    if args.path:
        target = Path(args.path)
    else:
        content = Path(__file__).resolve().parent.parent / "content"
        target = content / args.lang if args.lang else content

    if not target.exists():
        print(f"[plot] ERROR path not found: {target} (pass a content root explicitly)")
        sys.exit(1)

    files = [target] if target.is_file() else sorted(target.rglob("*.md"))
    total_errors = total_warns = scanned = 0

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").split("\n")
        except OSError as e:
            print(f"[plot] ERROR reading {f}: {e}")
            total_errors += 1
            continue
        for start, body in find_plot_blocks(lines):
            scanned += 1
            for level, msg in check_block(body):
                if level == "ERROR":
                    total_errors += 1
                    print(f"{f}:{start + 2}: ERROR {msg}")
                else:
                    total_warns += 1
                    print(f"{f}:{start + 2}: WARN  {msg}")

    print(f"[plot] scanned {scanned} plot block(s) in {len(files)} file(s); "
          f"{total_errors} error(s), {total_warns} warning(s)")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
