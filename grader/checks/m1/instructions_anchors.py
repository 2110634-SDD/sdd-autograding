# grader/checks/m1/instructions_anchors.py
from __future__ import annotations

from ._util import repo, read_text, item

ANCHORS = [
    "# Milestone 1: Foundations – Problem Understanding & High-Level Design",
    "## สิ่งที่ต้องส่ง (Deliverables)",
    "## สิ่งที่ **ไม่ควรทำ** ใน Milestone นี้",
    "[Student Fill In]",
    "รายละเอียดคะแนนดูได้จาก `PROJECT_SPEC.md`",
]


def run(ctx):
    rel = "milestone1/INSTRUCTIONS.md"
    path = repo(ctx) / "milestone1" / "INSTRUCTIONS.md"

    if not path.exists():
        return item(
            item_id="M1.CONTRACT.02",
            title="INSTRUCTIONS anchors intact",
            severity="BLOCKER",
            score=0,
            max_score=6,
            what_failed="ไม่พบ INSTRUCTIONS.md จึงตรวจ anchors ของ contract ไม่ได้",
            how_to_fix=[
                "Restore milestone1/INSTRUCTIONS.md กลับจาก assignment template repository",
                "ตรวจว่าไฟล์อยู่ path ถูกต้อง แล้วติด tag ส่งใหม่",
            ],
            evidence={"path": rel, "exists": False},
        )

    text = read_text(path)
    missing = [a for a in ANCHORS if a not in text]

    if not missing:
        return item(
            item_id="M1.CONTRACT.02",
            title="INSTRUCTIONS anchors intact",
            severity="BLOCKER",
            score=6,
            max_score=6,
            evidence={"path": rel, "exists": True, "missing_anchors": []},
        )

    # Keep evidence concise but useful
    preview = missing[:5]
    more = len(missing) - len(preview)

    return item(
        item_id="M1.CONTRACT.02",
        title="INSTRUCTIONS anchors intact",
        severity="BLOCKER",
        score=0,
        max_score=6,
        what_failed="INSTRUCTIONS.md ถูกแก้ไข/ไม่ตรง template (ขาด contract anchors ที่ต้องมี)",
        how_to_fix=[
            "Revert milestone1/INSTRUCTIONS.md กลับเป็นเวอร์ชันจาก template repository",
            "ห้ามแก้ไฟล์นี้ (เป็น contract)",
            "หลังแก้แล้วติด tag ส่งใหม่",
        ],
        evidence={
            "path": rel,
            "exists": True,
            "missing_anchors_preview": preview,
            "missing_anchors_count": len(missing),
            "missing_anchors_more": more if more > 0 else 0,
        },
    )