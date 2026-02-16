from ._util import repo, read_text
import re

def _count_ellipsis_lines(text: str) -> int:
    return len(re.findall(r"^\s*>\s*…\s*$", text, flags=re.MULTILINE))

def run(ctx):
    path = repo(ctx) / "milestone1" / "STUDENT_SUMMARY.md"
    if not path.exists():
        return 0, 12, "[BLOCKER] Missing milestone1/STUDENT_SUMMARY.md"

    text = read_text(path)
    issues = []

    # Section 1 placeholders?
    sec1 = re.search(r"##\s*1\..*?(?=##\s*2\.)", text, flags=re.DOTALL)
    sec1_text = sec1.group(0) if sec1 else ""
    if _count_ellipsis_lines(sec1_text) > 0:
        issues.append("Section 1 still has '> …' placeholders")

    # Out of scope filled?
    out_scope = re.search(r"\*\*ขอบเขตที่ไม่ครอบคลุม.*?\*\*([\s\S]*?)(?=\n---|\n##\s*2\.|\Z)", text)
    out_txt = (out_scope.group(1) if out_scope else "").strip()
    if not out_txt or "> …" in out_txt:
        issues.append("Out of scope missing/placeholder")

    # Key Use Case 1/2 name placeholders
    if re.search(r"\*\*Use Case 1:\*\*\s*`?<ชื่อ use case>`?", text):
        issues.append("Use Case 1 name is placeholder")
    if re.search(r"\*\*Use Case 2:\*\*\s*`?<ชื่อ use case>`?", text):
        issues.append("Use Case 2 name is placeholder")

    # QA1 placeholder
    if re.search(r"\*\*Quality Attribute 1:\*\*\s*`?<ชื่อ quality attribute>`?", text):
        issues.append("Quality Attribute 1 is placeholder")

    # Trade-off filled (soft)
    qa1 = re.search(r"\*\*Quality Attribute 1:.*?(?=\*\*Quality Attribute 2|\n##\s*4\.|\Z)", text, flags=re.DOTALL)
    qa1_block = qa1.group(0) if qa1 else ""
    trade = re.search(r"Trade-off.*?:\s*(.*)", qa1_block)
    if not trade or not trade.group(1).strip() or "…" in trade.group(1):
        issues.append("QA trade-off missing/empty")

    # Open questions bullets >=2 (soft)
    oq = re.search(r"ประเด็นหรือความเสี่ยง.*?\n([\s\S]*?)(?=\n---|\Z)", text)
    oq_block = oq.group(1) if oq else ""
    bullets = [ln for ln in oq_block.splitlines() if ln.strip().startswith("-")]
    if len(bullets) < 2:
        issues.append("Open questions/risks < 2 bullets")

    if not issues:
        return 12, 12, "OK: STUDENT_SUMMARY.md minimums filled"

    score = max(0, 12 - 2 * len(issues))
    return score, 12, (
        "[MAJOR] STUDENT_SUMMARY.md is incomplete\n"
        f"Issues: {', '.join(issues)}\n"
        "Why: This document captures design reasoning (why), scope, QA drivers, and open questions.\n"
        "Fix:\n"
        "- Replace all '> …' placeholders with real content.\n"
        "- Provide at least 1 out-of-scope item.\n"
        "- Fill UC1/UC2 names and QA driver + trade-off.\n"
        "- Add 2–3 risks to validate in M2."
    )
