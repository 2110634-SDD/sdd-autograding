# grader/checks/m1/manifest.py
from __future__ import annotations

from ._util import repo, item

CORE = [
    "milestone1/README.md",
    "milestone1/STUDENT_SUMMARY.md",
    "milestone1/concrete-quality-attribute-scenarios.md",
    "milestone1/use-case-descriptions/README.md",
    "milestone1/diagrams/README.md",
]


def run(ctx):
    r = repo(ctx)
    missing = [p for p in CORE if not (r / p).exists()]

    if not missing:
        return item(
            item_id="M1.MANIFEST.01",
            title="Milestone1 required files exist (core)",
            severity="BLOCKER",
            score=8, max_score=8,
            evidence={"checked_count": len(CORE), "missing": []},
        )

    score = max(0, 8 - 2 * len(missing))
    return item(
        item_id="M1.MANIFEST.01",
        title="Milestone1 required files exist (core)",
        severity="BLOCKER",
        score=score, max_score=8,
        what_failed="โครงสร้างไฟล์ milestone1 ไม่ครบตาม manifest (core)",
        how_to_fix=[
            "สร้างไฟล์ที่ขาดให้ครบ (path ต้องตรงเป๊ะ)",
            "commit แล้วติด tag ส่งใหม่",
        ],
        evidence={"checked_count": len(CORE), "missing": missing, "missing_count": len(missing)},
    )