# grader/checks/m1/readme_overview_filled.py
from __future__ import annotations

from ._util import repo, read_text, item

PLACEHOLDERS = [
    "[Student Fill In]",
    "(อธิบายปัญหาโดยสรุป 2–3 บรรทัด)",
]


def run(ctx):
    rel = "milestone1/README.md"
    path = repo(ctx) / "milestone1" / "README.md"

    if not path.exists():
        return item(
            item_id="M1.README.FILL",
            title="milestone1/README.md filled (overview + no template markers)",
            severity="BLOCKER",
            score=0,
            max_score=8,
            what_failed="ไม่พบไฟล์ milestone1/README.md",
            how_to_fix=[
                "สร้าง milestone1/README.md ตาม template",
                "เติมหัวข้อ ## Overview และลบ marker/placeholder ให้ครบ",
                "commit แล้วติด tag ส่งใหม่",
            ],
            evidence={"path": rel, "exists": False},
        )

    text = read_text(path)

    issues = []
    if "## Overview" not in text:
        issues.append("Missing section: ## Overview")
    if "[Student Fill In]" in text:
        issues.append("Still contains: [Student Fill In]")
    for ph in PLACEHOLDERS[1:]:
        if ph in text:
            issues.append(f"Still contains placeholder: {ph}")

    if not issues:
        return item(
            item_id="M1.README.FILL",
            title="milestone1/README.md filled (overview + no template markers)",
            severity="MAJOR",
            score=8,
            max_score=8,
            evidence={"path": rel, "exists": True, "issues": []},
        )

    # scoring: each issue costs 2 points (cap at 0)
    score = max(0, 8 - 2 * len(issues))

    return item(
        item_id="M1.README.FILL",
        title="milestone1/README.md filled (overview + no template markers)",
        severity="MAJOR",
        score=score,
        max_score=8,
        what_failed="milestone1/README.md ยังกรอกไม่ครบ/ยังมี marker จาก template",
        how_to_fix=[
            "เพิ่มหัวข้อ ## Overview แล้วเขียนสรุป 2–3 บรรทัด (ปัญหา, ผู้ใช้หลัก, เป้าหมายหลักของระบบ)",
            "ลบ [Student Fill In] และ placeholder ทั้งหมดออก",
            "commit แล้วติด tag ส่งใหม่",
        ],
        evidence={"path": rel, "exists": True, "issues": issues, "issues_count": len(issues)},
    )