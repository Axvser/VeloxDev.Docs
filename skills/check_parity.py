"""
check_parity.py

Guard against EN/ZH skill drift: `skills/SKILL.md` is a single artifact regenerated
per language (`gen_skill.py --lang en|zh`), so only the language built last is
committed. Because a bilingual child wiki can be driven by whichever language build
an agent loaded, the two builds must stay rule-equivalent. This script regenerates
both builds in a temp copy and
asserts that a curated set of RULES is present in one language iff present in the
other (technical tokens like script names are identical across languages; rule
phrases are mapped en→zh).

This is a parity smoke test, not a translation diff: it catches "the zh module
lagged behind and lost rule X", not wording polish. Run it manually before committing
skill changes; nothing invokes it automatically.

Usage:
    python skills/check_parity.py
Exit code: 0 = rules in parity, 1 = at least one rule lives in only one language.
"""

import os
import shutil
import subprocess
import sys
import tempfile

SKILLS_ROOT = os.path.abspath(os.path.dirname(__file__))

# (en_marker, zh_marker): both must appear in their language build, or neither may.
# Identical technical tokens first (script names, thresholds, flags), then mapped phrases.
PARITY_PAIRS = [
    # technical tokens (untranslated)
    ("index.md", "index.md"),
    ("300", "300"),
    ("validate-structure.py", "validate-structure.py"),
    ("validate-links.py", "validate-links.py"),
    ("validate-plantuml.py", "validate-plantuml.py"),
    ("validate-mermaid.js", "validate-mermaid.js"),
    ("validate-katex.js", "validate-katex.js"),
    ("validate-mermaid.py", "validate-mermaid.py"),
    ("validate-katex.py", "validate-katex.py"),
    ("validate-titles.py", "validate-titles.py"),
    ("validate-plot.py", "validate-plot.py"),
    ("gen_tree.py", "gen_tree.py"),
    ("--strict", "--strict"),
    ("tel:", "tel:"),
    ("Templates/welcome-default.md", "Templates/welcome-default.md"),
    ("Run Declaration", "运行声明"),
    ("title-allowlist.json", "title-allowlist.json"),
    ("feat-link", "feat-link"),
    # rule phrases (mapped)
    ("Feature Inventory", "功能清单"),
    ("Coverage Reconciliation Matrix", "覆盖率对账矩阵"),
    ("HARD GATE", "硬性关卡"),
    ("Prerequisites", "前置条件"),
    ("TargetFrameworks", "TargetFrameworks"),
    ("Code Authenticity", "代码真实性"),
    ("`index.md` exists in **every**", "每个页面目录（根目录和子页面）都存在"),
    # hierarchy / outline-first rules (added with page-size gate)
    ("Page-focus limit", "页面聚焦上限"),
    ("Outline-first", "大纲先行"),
    ("leaf budget", "叶子预算"),
    ("cg:atomic", "cg:atomic"),
    # title hygiene / localisation / welcome-page / plot rules
    ("code identifier", "代码标识符"),
    ("Title & Localisation Audit", "标题与本地化审计"),
    ("Welcome Page Audit", "欢迎页审计"),
    ("Rendered Content Members", "渲染成员"),
    ("Function plot rules", "函数图像书写规范"),
    # heading-repetition rules
    ("restates the heading above it", "重复其上方标题"),
    ("dimension echo", "维度回声"),
]


def run_gen(temp_skills: str, lang: str) -> str:
    gen = os.path.join(temp_skills, "gen_skill.py")
    out = os.path.join(temp_skills, "SKILL.md")
    result = subprocess.run(
        [sys.executable, gen, "--lang", lang],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=temp_skills,
    )
    if result.returncode != 0:
        print(f"[parity] ERROR gen_skill --lang {lang} failed:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
        sys.exit(2)
    with open(out, encoding="utf-8") as f:
        return f.read()


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    tmp = tempfile.mkdtemp(prefix="cloudglyph_parity_")
    try:
        temp_skills = os.path.join(tmp, "skills")
        shutil.copytree(SKILLS_ROOT, temp_skills,
                        ignore=shutil.ignore_patterns("__pycache__", ".git", ".github"))
        en_out = run_gen(temp_skills, "en")
        zh_out = run_gen(temp_skills, "zh")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    problems = 0
    for en_marker, zh_marker in PARITY_PAIRS:
        in_en = en_marker in en_out
        in_zh = zh_marker in zh_out
        if in_en != in_zh:
            problems += 1
            if in_en and not in_zh:
                print(f"[parity] ERROR rule present in EN but missing in ZH: '{en_marker}'")
            else:
                print(f"[parity] ERROR rule present in ZH but missing in EN: '{zh_marker}'")

    # Structure sanity: both builds must contain the same number of module sections.
    # gen_skill inserts one `> {pipeline}.{description}` marker per module (see
    # generate_workflow_with_content), so counting those guards against a module
    # silently failing to assemble in one language.
    def module_count(text: str) -> int:
        return sum(1 for line in text.splitlines() if line.startswith("> ") and line[2:3].isdigit() and "." in line[2:])

    n_en, n_zh = module_count(en_out), module_count(zh_out)
    if n_en != n_zh:
        problems += 1
        print(f"[parity] ERROR module-section count differs: EN={n_en} ZH={n_zh}")

    print(f"[parity] EN build {len(en_out)} bytes, ZH build {len(zh_out)} bytes; {problems} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
