# grader/checks/m1/manifest.py
from __future__ import annotations
from pathlib import Path
from grader.core.models import Severity
from grader.checks.m1.common import ok, fail, msg


CORE_FILES = [
    "milestone1/README.md",
    "milestone1/STUDENT_SUMMARY.md",
    "milestone1/concrete-quality-attribute-scenarios.md",
    "milestone1/use-case-descriptions/README.md",
    "milestone1/diagrams/README.md",
]


def check_manifest_core(repo: Path):
    check_id = "M1.MANIFEST.01"
    title = "Milestone1 core files exist"
    possible = 8

    missing = []
    for rel in CORE_FILES:
        if not (repo / rel).exists():
            missing.append(rel)

    if not missing:
        return ok(check_id, title, possible)

    # Capped penalty: earned decreases proportionally but not below 0
    earned = max(0, possible - len(missing) * 2)
    return fail(
        check_id, title, earned, possible,
        [msg(
            Severity.BLOCKER,
            f"Missing required milestone1 files: {', '.join(missing)}",
            "โครงสร้างไฟล์เป็นส่วนของ contract และใช้เป็น baseline สำหรับการตรวจส่วนอื่น ๆ",
            ["Create the missing files at the exact paths.", "Commit and push again."],
            evidence="; ".join(missing),
        )],
        debug={"missing": missing},
    )
