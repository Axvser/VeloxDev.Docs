"""
validate-mermaid.py

Deterministic structural validation of Mermaid blocks in Markdown wiki content.
Use this in the skill's Review phase instead of relying on the agent's eye.

Checks (per ```mermaid fenced block):
  ERROR  non-empty diagram, recognized type on the header line
  ERROR  balanced brackets [ ] ( ) { } across the block
  ERROR  sequenceDiagram: alt/else/end and loop/end pairing
  ERROR  flowchart/graph: a valid direction (TD/TB/LR/RL/BT) on the header
  WARN   flowchart edge token that looks like a malformed arrow

Usage:
    python validate-mermaid.py                  # auto-detect content root
    python validate-mermaid.py --lang en
    python validate-mermaid.py <dir-or-file>

Exit code: 0 = clean, 1 = at least one ERROR.
"""

import argparse
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^```\s*mermaid\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")

_HEADER_RE = re.compile(r"^(flowchart|graph|classDiagram|sequenceDiagram|stateDiagram-v2|"
                        r"gantt|pie|journey|gitGraph|erDiagram|timeline|block-beta)\b")
_DIRECTION = ("TD", "TB", "LR", "RL", "BT")
_EDGE_TOKENS = ("-->", "---", "-.->", "==>", "--->", "---x", "--o", "-.", "=>", "<-->", "<---", "<==>")
_EDGE_RE = re.compile(r"[<\-=\.>]{2,}")


def find_blocks(lines):
    blocks = []
    i = 0
    while i < len(lines):
        if FENCE_OPEN.match(lines[i].strip()):
            j = i + 1
            while j < len(lines) and not FENCE_CLOSE.match(lines[j].strip()):
                j += 1
            blocks.append((i, j, lines[i + 1 : j]))
            i = j + 1
        else:
            i += 1
    return blocks


def balanced(s, open_ch, close_ch):
    return s.count(open_ch) == s.count(close_ch)


def validate_block(block_lines):
    issues = []
    body = [l.strip() for l in block_lines if l.strip()]
    if not body:
        return [("ERROR", "empty mermaid block")]
    text = "\n".join(body)
    header = body[0]

    m = _HEADER_RE.match(header)
    if not m:
        issues.append(("ERROR", f"unrecognized mermaid type on header line: {header!r}"))
        return issues
    kind = m.group(1)

    # bracket balance
    for o, c, name in (("[", "]", "[ ]"), ("(", ")", "( )"), ("{", "}", "{ }")):
        if not balanced(text, o, c):
            issues.append(("ERROR", f"unbalanced {name} brackets"))

    if kind in ("flowchart", "graph"):
        dirm = re.search(r"(?:flowchart|graph)\s+(TD|TB|LR|RL|BT)\b", header)
        if not dirm:
            issues.append(("ERROR", f"flowchart direction missing/invalid on header (expected one of {_DIRECTION})"))
        # arrow sanity: any token of arrow chars must contain a known arrow
        for tok in re.findall(r"[<\-=\.>]{2,}", text):
            if tok not in _EDGE_TOKENS and tok not in ("<|--", "--|>", "o--", "--o", "x--", "--x"):
                issues.append(("WARN", f"unusual edge token {tok!r}"))

    elif kind == "sequenceDiagram":
        openers = sum(1 for l in body if re.match(r"^(alt|loop|opt|par|critical)\b", l))
        closers = sum(1 for l in body if re.match(r"^end\b", l))
        if openers != closers:
            issues.append(("ERROR", f"{openers} alt/loop/opt block(s) vs {closers} 'end'"))

    elif kind == "classDiagram":
        # relations use <|--, -->, o--, ..|> etc.; just check an arrow-ish token exists if there are lines
        pass

    return issues


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Validate Mermaid blocks in wiki Markdown")
    parser.add_argument("path", nargs="?", help="file or directory to scan (default: auto-detect content root)")
    parser.add_argument("--lang", help="only scan this language subdir (e.g. en, zh)")
    args = parser.parse_args()

    if args.path:
        target = Path(args.path)
    else:
        content = Path(__file__).resolve().parent.parent / "content"
        target = content / args.lang if args.lang else content

    files = [target] if target.is_file() else sorted(target.rglob("*.md"))
    total_errors = total_warns = scanned = 0

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").split("\n")
        except OSError as e:
            print(f"[mermaid] ERROR reading {f}: {e}")
            total_errors += 1
            continue
        for start, end, block in find_blocks(lines):
            scanned += 1
            for level, msg in validate_block(block):
                if level == "ERROR":
                    total_errors += 1
                    print(f"{f}:{start + 2}: ERROR {msg}")
                else:
                    total_warns += 1
                    print(f"{f}:{start + 2}: WARN  {msg}")

    print(f"[mermaid] scanned {scanned} block(s) in {len(files)} file(s); "
          f"{total_errors} error(s), {total_warns} warning(s)")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
