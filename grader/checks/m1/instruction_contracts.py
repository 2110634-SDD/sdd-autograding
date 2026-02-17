# grader/checks/m1/instruction_contracts.py
from __future__ import annotations

import re
from typing import Any, Dict, List

from ._util import repo, read_text, item, evidence_path

INSTR_PATH = "milestone1/INSTRUCTIONS.md"

ANCHORS = [
    "# Milestone 1: Foundations – Problem Understanding & High-Level Design",
    "## สิ่งที่ต้องส่ง (Deliverables)",
    "## สิ่งที่ **ไม่ควรทำ** ใน Milestone นี้",
    "[Student Fill In]",
    "รายละเอียดคะแนนดูได้จาก `PROJECT_SPEC.md`",
]


def _normalize_for_hash(s: str) -> str:
    # minimal normalization (safe): normalize newlines + trim trailing spaces
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.rstrip() for line in s.splitlines())
    # collapse multiple blank lines
    s = re.sub(r"\n{3,}", "\n\n", s).strip() + "\n"
    return s


def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run_all(ctx, *, strict_hash: bool = False, canonical_hash: str = "") -> List[Dict[str, Any]]:
    r = repo(ctx)
    p = r / INSTR_PATH

    out: List[Dict[str, Any]] = []

    # CONTRACT.01
    if p.exists():
        out.append(item(
            item_id="M1.CONTRACT.01",
            title="INSTRUCTIONS.md exists",
            severity="BLOCKER",
            score=2, max_score=2,
            evidence={**evidence_path(INSTR_PATH, True)},
        ))
    else:
        out.append(item(
            item_id="M1.CONTRACT.01",
            title="INSTRUCTIONS.md exists",
            severity="BLOCKER",
            score=0, max_score=2,
            what_failed="ไม่พบไฟล์ milestone1/INSTRUCTIONS.md",
            how_to_fix=[
                "Restore milestone1/INSTRUCTIONS.md กลับจาก assignment template repository",
                "ตรวจว่า path ตรง milestone1/INSTRUCTIONS.md แล้วติด tag ส่งใหม่",
            ],
            evidence={**evidence_path(INSTR_PATH, False)},
        ))
        # ถ้าไม่เจอไฟล์ ก็จบ contract checks อื่น
        out.append(item(
            item_id="M1.CONTRACT.02",
            title="INSTRUCTIONS anchors intact",
            severity="BLOCKER",
            score=0, max_score=6,
            what_failed="ไม่พบ INSTRUCTIONS.md จึงตรวจ anchors ของ contract ไม่ได้",
            how_to_fix=["Restore milestone1/INSTRUCTIONS.md จาก template แล้วส่งใหม่"],
            evidence={**evidence_path(INSTR_PATH, False)},
        ))
        # optional hash
        if strict_hash:
            out.append(item(
                item_id="M1.CONTRACT.03",
                title="INSTRUCTIONS normalized-hash unchanged (strict)",
                severity="MAJOR",
                score=0, max_score=4,
                what_failed="ไม่พบ INSTRUCTIONS.md จึงตรวจ hash ไม่ได้",
                how_to_fix=["Restore milestone1/INSTRUCTIONS.md จาก template แล้วส่งใหม่"],
                evidence={**evidence_path(INSTR_PATH, False)},
            ))
        return out

    # CONTRACT.02 anchors
    text = read_text(p)
    missing = [a for a in ANCHORS if a not in text]
    if not missing:
        out.append(item(
            item_id="M1.CONTRACT.02",
            title="INSTRUCTIONS anchors intact",
            severity="BLOCKER",
            score=6, max_score=6,
            evidence={**evidence_path(INSTR_PATH, True), "missing_anchors": []},
        ))
    else:
        out.append(item(
            item_id="M1.CONTRACT.02",
            title="INSTRUCTIONS anchors intact",
            severity="BLOCKER",
            score=0, max_score=6,
            what_failed="INSTRUCTIONS.md ถูกแก้/ไม่ตรง template (ขาด contract anchors ที่ต้องมี)",
            how_to_fix=[
                "Revert milestone1/INSTRUCTIONS.md กลับเป็นเวอร์ชันจาก template repository",
                "ห้ามแก้ไฟล์นี้ (เป็น contract)",
                "ติด tag ส่งใหม่",
            ],
            evidence={**evidence_path(INSTR_PATH, True), "missing_anchors": missing[:8], "missing_count": len(missing)},
        ))

    # CONTRACT.03 optional strict hash (ปิดไว้ default)
    if strict_hash:
        norm = _normalize_for_hash(text)
        h = _sha256(norm)
        passed = (canonical_hash and h == canonical_hash)
        out.append(item(
            item_id="M1.CONTRACT.03",
            title="INSTRUCTIONS normalized-hash unchanged (strict)",
            severity="MAJOR",
            score=4 if passed else 0,
            max_score=4,
            what_failed="INSTRUCTIONS.md normalized-hash ไม่ตรง canonical template" if not passed else "",
            how_to_fix=[
                "ถ้าไม่ได้ตั้งใจแก้: revert milestone1/INSTRUCTIONS.md กลับจาก template",
                "ถ้าคุณเป็นผู้สอน: อัปเดต canonical_hash ใน autograder",
            ] if not passed else [],
            evidence={**evidence_path(INSTR_PATH, True), "computed_hash": h, "canonical_hash": canonical_hash},
        ))

    return out