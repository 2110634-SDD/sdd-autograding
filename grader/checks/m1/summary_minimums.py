# grader/checks/m1/summary_minimums.py
from __future__ import annotations

import re

from ._util import repo, read_text, item


def _count_ellipsis_lines(text: str) -> int:
    return len(re.findall(r"^\s*>\s*…\s*$", text, flags=re.MULTILINE))


def run(ctx):
    rel = "milestone1/STUDENT_SUMMARY.md"
    path = repo(ctx) / "milestone1" / "STUDENT_SUMMARY.md"

    if not path.exists():
        return item(
            item_id="M1.SUMMARY.MIN",
            title="STUDENT_SUMMARY.md minimums filled",
            severity="BLOCKER",
            score=0,
            max_score=12,
            what_failed="ไม่พบไฟล์ milestone1/STUDENT_SUMMARY.md",
            how_to_fix=[
                "สร้าง milestone1/STUDENT_SUMMARY.md ตาม template",
                "กรอกส่วนที่เป็น placeholder ให้ครบ แล้ว commit",
                "ติด tag ส่งใหม่",
            ],
            evidence={"path": rel, "exists": False},
        )

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
        return item(
            item_id="M1.SUMMARY.MIN",
            title="STUDENT_SUMMARY.md minimums filled",
            severity="MAJOR",
            score=12,
            max_score=12,
            evidence={"path": rel, "exists": True, "issues": []},
        )

    score = max(0, 12 - 2 * len(issues))

    return item(
        item_id="M1.SUMMARY.MIN",
        title="STUDENT_SUMMARY.md minimums filled",
        severity="MAJOR",
        score=score,
        max_score=12,
        what_failed="STUDENT_SUMMARY.md ยังกรอกไม่ครบตาม minimum requirements",
        how_to_fix=[
            "แทนที่ทุกบรรทัดที่เป็น '> …' ด้วยเนื้อหาจริง",
            "เติม Out of scope อย่างน้อย 1 ข้อ (เป็น bullet/ข้อความจริง ไม่ใช่ placeholder)",
            "ใส่ชื่อ UC1/UC2 และ Quality Attribute driver ให้เป็นคำจริง (ไม่ใช่ <...>)",
            "เขียน Trade-off ที่มีเนื้อหา และเพิ่มความเสี่ยง/คำถามอย่างน้อย 2 bullet",
            "commit แล้วติด tag ส่งใหม่",
        ],
        evidence={
            "path": rel,
            "exists": True,
            "issues": issues,
            "issues_count": len(issues),
            "scoring": {"rule": "12 - 2*issues", "min": 0},
        },
    )