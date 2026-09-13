"""
validate-plantuml.py

Deterministic structural validation of PlantUML blocks in Markdown wiki content.
Use this in the skill's Review phase instead of relying on the agent's eye.

Checks (per ```plantuml fenced block):
  ERROR  @startuml / @enduml pairing (one each per block, none dangling)
  ERROR  brace balance { } within the block
  ERROR  alt/opt/loop/par/break/critical/group openers vs `end` closers
  WARN   activate vs deactivate imbalance (note: `return`/`@enduml` may legally close a
         scope, so an imbalance is a strong hint, not a guaranteed error)
  WARN   participant aliases referenced before declaration (informational: PlantUML
         auto-creates undeclared participants, so this is advisory only)

Usage:
    python validate-plantuml.py                  # auto-detect content root, all languages
    python validate-plantuml.py --lang en        # only one language dir
    python validate-plantuml.py <dir-or-file>    # scan an explicit path

Exit code: 0 = clean, 1 = at least one ERROR (warnings alone do not fail).
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_OPENERS = ("alt", "opt", "loop", "par", "break", "critical", "group")
# Participant declaration keywords: alias is the token after the keyword (or the quoted
# label's trailing alias) on the same line.
_DECL_RE = re.compile(
    r"^(actor|participant|database|queue|collections|boundary|control|entity|package)\s+"
    r"(?P<name>\"(?:[^\"]|\\.)*\"|[A-Za-z0-9_]+)"
    r"(?:\s+as\s+(?P<alias>[A-Za-z0-9_]+))?",
)
_MESSAGE_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*([-.]{1,3}>|<[-.]{1,3}|<->)\s*([A-Za-z0-9_]+)\s*:")

FENCE_OPEN = re.compile(r"^```\s*plantuml\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")


def find_blocks(lines):
    """Yield (start_idx, end_idx, block_lines) for every plantuml fence."""
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


def validate_with_java(block_lines, jar):
    """Real PlantUML validation: run `java -jar plantuml.jar -checkonly` on the block.

    `-checkonly` returns exit code 0 even on syntax errors, so the *output* is the
    signal: it prints "Some diagram description contains errors" on failure.
    Returns list of (level, message); [] when the real engine accepts the diagram.
    """
    text = "\n".join(block_lines)
    fd, tmp = tempfile.mkstemp(suffix=".puml")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tf:
            tf.write(text + "\n")
        r = subprocess.run(
            ["java", "-jar", str(jar), "-checkonly", tmp],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        out = (r.stdout + r.stderr)
        if r.returncode != 0 or "contains errors" in out.lower() or "Exception" in out:
            detail = next((l for l in out.splitlines() if l.strip()), out)
            return [("ERROR", f"plantuml engine rejected block: {detail[:160]}")]
    except FileNotFoundError:
        return [("ERROR", "java not found on PATH — cannot run plantuml.jar")]
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return []


def validate_block(block_lines):
    """Return list of (level, message). level in {'ERROR','WARN'}."""
    issues = []
    text = "\n".join(block_lines)
    body = [l.strip() for l in block_lines if l.strip()]

    # @startuml / @enduml pairing
    starts = sum(1 for l in body if re.match(r"@startuml\b", l))
    ends = sum(1 for l in body if re.match(r"@enduml\b", l))
    if starts == 0:
        issues.append(("ERROR", "no @startuml marker"))
    if ends == 0:
        issues.append(("ERROR", "no @enduml marker"))
    if starts > 1 or ends > 1:
        issues.append(("ERROR", f"{starts} @startuml / {ends} @enduml — expected one of each"))

    # brace balance
    if text.count("{") != text.count("}"):
        issues.append(("ERROR", f"unbalanced braces: {text.count('{')} '{{' vs {text.count('}')} '}}'"))

    # alt/opt/loop/... vs end
    openers = sum(1 for l in body if re.match(r"^(?:alt|opt|loop|par|break|critical|group)\b", l))
    ends_count = sum(1 for l in body if re.match(r"^end\b", l) and not re.match(r"^end\s+note\b", l))
    if openers != ends_count:
        issues.append(("ERROR", f"{openers} block openers (alt/opt/loop/par/...) vs {ends_count} 'end' closers"))

    # activate / deactivate (keyword forms only; accelerator `X ++`/`X --` is skipped
    # because `--` also appears in arrow tokens like `-->` and would false-positive)
    act = sum(1 for l in body if re.match(r"^activate\b", l))
    deact = sum(1 for l in body if re.match(r"^deactivate\b", l))
    if act != deact:
        issues.append(
            ("WARN", f"{act} activate(s) vs {deact} deactivate(s) — check pairing "
                     f"('return' or end of block may legally close a scope)")
        )

    # participant declarations + references
    declared = set()
    for l in body:
        m = _DECL_RE.match(l)
        if m:
            declared.add((m.group("alias") or m.group("name")).strip('"'))
    undeclared = []
    for l in body:
        m = _MESSAGE_RE.match(l)
        if m and not re.match(r"^(actor|participant|database|queue|collections|boundary|control|entity|package)\b", l):
            for ref in (m.group(1), m.group(3)):
                if ref not in declared and ref not in {"User", "Client", "Actor"}:
                    undeclared.append(ref)
    if undeclared:
        issues.append(("WARN", f"participant(s) referenced without declaration: {sorted(set(undeclared))} "
                               f"(PlantUML auto-creates them — advisory only)"))

    return issues


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Validate PlantUML blocks in wiki Markdown")
    parser.add_argument("path", nargs="?", help="file or directory to scan (default: auto-detect content root)")
    parser.add_argument("--lang", help="only scan this language subdir (e.g. en, zh)")
    parser.add_argument("--engine", choices=["structural", "java"], default="structural",
                        help="structural = heuristic pre-check (no deps); java = run the real "
                             "plantuml.jar -checkonly engine (needs java + plantuml.jar)")
    parser.add_argument("--jar", default=None, help="path to plantuml.jar (default: next to this script)")
    args = parser.parse_args()

    if args.path:
        target = Path(args.path)
    else:
        content = Path(__file__).resolve().parent.parent / "content"
        target = content / args.lang if args.lang else content

    jar = Path(args.jar) if args.jar else Path(__file__).resolve().parent / "plantuml.jar"
    use_java = args.engine == "java"
    if use_java and not jar.exists():
        print(f"[plantuml] ERROR: plantuml.jar not found at {jar} (download it or pass --jar)")
        sys.exit(1)

    files = [target] if target.is_file() else sorted(target.rglob("*.md"))
    total_errors = 0
    total_warns = 0
    scanned = 0

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").split("\n")
        except OSError as e:
            print(f"[plantuml] ERROR reading {f}: {e}")
            total_errors += 1
            continue
        for start, end, block in find_blocks(lines):
            scanned += 1
            issues = validate_with_java(block, jar) if use_java else validate_block(block)
            for level, msg in issues:
                if level == "ERROR":
                    total_errors += 1
                    print(f"{f}:{start + 2}: ERROR {msg}")
                else:
                    total_warns += 1
                    print(f"{f}:{start + 2}: WARN  {msg}")

    print(f"[plantuml] scanned {scanned} block(s) in {len(files)} file(s); "
          f"{total_errors} error(s), {total_warns} warning(s)")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
