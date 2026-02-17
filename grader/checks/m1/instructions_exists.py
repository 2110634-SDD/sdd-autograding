# grader/checks/m1/instructions_exists.py
from __future__ import annotations

from ._util import repo, item


def run(ctx):
    p = repo(ctx) / "milestone1" / "INSTRUCTIONS.md"

    if p.exists():
        return item(
            item_id="M1.CONTRACT.01",
            title="INSTRUCTIONS.md exists",
            severity="BLOCKER",
            score=2,
            max_score=2,
            evidence={"path": "milestone1/INSTRUCTIONS.md", "exists": True},
        )

    return item(
        item_id="M1.CONTRACT.01",
        title="INSTRUCTIONS.md exists",
        severity="BLOCKER",
        score=0,
        max_score=2,
        what_failed="ไม่พบไฟล์ milestone1/INSTRUCTIONS.md",
        how_to_fix=[
            "Restore milestone1/INSTRUCTIONS.md กลับจาก assignment template repository",
            "ตรวจว่า path เป็น milestone1/INSTRUCTIONS.md (ตัวพิมพ์เล็ก/ใหญ่ต้องตรง) แล้วติด tag ส่งใหม่",
        ],
        evidence={"path": "milestone1/INSTRUCTIONS.md", "exists": False},
    )